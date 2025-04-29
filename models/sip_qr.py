# -*- coding: utf-8 -*-

import logging

import requests
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class KyoheiSipApiSipQr(models.Model):
    _name = 'sip.qr'
    _description = 'SIP QR'
    _rec_name = 'sequence_id'
    _order = 'sequence_id desc'

    sequence_id = fields.Char(readonly=True, string='Secuencia')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence_id') or vals['sequence_id'] == '/':
                vals['sequence_id'] = self.env['ir.sequence'].next_by_code('sip.qr.sequence') or '/'
        return super(KyoheiSipApiSipQr, self).create(vals_list)

    state = fields.Selection(
        [('pendiente', 'Pendiente'),
         ('inhabilitado', 'Inhabilitado'),
         ('error', 'Error'),
         ('expirado', 'Expirado'),
         ('pagado', 'Pagado'),],
        string='Entorno SIP',
        default='dev'
    )
    source_model = fields.Char(string='Modelo')
    source_res_id = fields.Char(string='ID origen')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    # QR generation data
    payment_provider_id = fields.Many2one('payment.provider', string='Proveedor de pagos')
    company_id = fields.Many2one('res.company', string='Company')
    ref = fields.Char(string='Alias')
    label = fields.Char(string='Detalle')
    amount = fields.Monetary(string='Monto')
    currency_id = fields.Many2one('res.currency', string='Divisa')
    date = fields.Date(string='Fecha vencimiento')
    for_single_use = fields.Boolean(string='Uso único')
    journal_id = fields.Many2one(related='payment_provider_id.journal_id', string='Diario')
    obfuscated_account = fields.Char(string='Cuenta destino')
    qr_image = fields.Binary()

    def _get_qr_apikey(self):
        payment_provider_id = self.payment_provider_id
        return payment_provider_id.sip_qr_prod_apikey if payment_provider_id.state == 'enabled' else payment_provider_id.sip_qr_dev_apikey

    def _get_sip_url(self):
        payment_provider_id = self.payment_provider_id
        sip_url_param = 'sip_prod_url' if payment_provider_id.state == 'enabled' else 'sip_dev_url'
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_sip_api.{sip_url_param}")
        return sip_url

    def _disable_sip_qr(self):
        payment_provider_id = self.payment_provider_id
        self.env['account.move']._check_sip_auth_token(payment_provider_id)
        sip_url = self._get_sip_url()
        url = sip_url + '/api/v1/inhabilitarPago'
        headers = {
            'apikeyServicio': self._get_qr_apikey(),
            'Authorization': f'Bearer {payment_provider_id.sip_auth_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url=url, headers=headers, json={'alias': self.ref})
            response_data = response.json()
            _logger.info("SIP QR status: %s", response.status_code)
            _logger.info("Response: %s", response.text)
            if response.status_code == 200:
                if response_data['codigo'] == '0000':
                    self.write({'state': 'inhabilitado'})
                    if self.source_model and self.source_res_id:
                        self.env[self.source_model].sudo().search([('id', '=', self.source_res_id)]).sudo().write({'sip_qr_id': False, 'qr_attachment_id': False})
                _logger.info(response_data['mensaje'])
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))

    def action_disable_sip_qr(self):
        for record in self:
            record._disable_sip_qr()

    def _check_sip_state(self):
        payment_provider_id = self.payment_provider_id
        self.env['account.move']._check_sip_auth_token(payment_provider_id)
        sip_url = self._get_sip_url()
        url = sip_url + '/api/v1/estadoTransaccion'
        headers = {
            'apikeyServicio': self._get_qr_apikey(),
            'Authorization': f'Bearer {payment_provider_id.sip_auth_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url=url, headers=headers, json={'alias': self.ref})
            response_data = response.json()
            _logger.info("SIP QR status: %s", response.status_code)
            _logger.info("Response: %s", response.text)
            if response.status_code == 200:
                if response_data['codigo'] == '0000':
                    sip_token = response.json()['objeto']['estadoActual']
                    self.state = sip_token.lower()
                elif response_data['codigo'] == '9999':
                    self.state = 'expirado'
                _logger.info(response_data['mensaje'])
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))

    def action_check_sip_state(self):
        for record in self:
            record._check_sip_state()
