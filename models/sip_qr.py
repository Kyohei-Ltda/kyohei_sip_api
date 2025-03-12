# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class KyoheiBankIntegrationsSipQr(models.Model):
    _name = 'sip.qr'
    _description = 'SIP QR'
    _rec_name = 'sequence_id'

    sequence_id = fields.Char(readonly=True, string='Secuencia')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence_id') or vals['sequence_id'] == '/':
                vals['sequence_id'] = self.env['ir.sequence'].next_by_code('sip.qr.sequence') or '/'
        return super(KyoheiBankIntegrationsSipQr, self).create(vals_list)

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
    company_id = fields.Many2one('res.company', string='Company')
    ref = fields.Char(string='Alias')
    label = fields.Char(string='Detalle')
    amount = fields.Monetary(string='Monto')
    currency_id = fields.Many2one('res.currency', string='Divisa')
    date = fields.Date(string='Fecha vencimiento')
    for_single_use = fields.Boolean(string='Uso único')
    journal_id = fields.Many2one('account.journal', string='Diario')
    obfuscated_account = fields.Char(string='Cuenta destino')
    qr_image = fields.Binary()

    def _get_journal_id(self):
        obfuscated_account = self.obfuscated_account
        if obfuscated_account and not self.journal_id:
            pattern = obfuscated_account.replace("X", "_")
            partner_bank = self.env['res.partner.bank'].search([('acc_number', "like", pattern)], limit=1)
            journal_id = self.env['account.journal'].search([('type', "=", 'bank'), ('bank_account_id', '=', partner_bank.id)], limit=1)
            if journal_id:
                self.journal_id = journal_id.id

    def action_get_journal_id(self):
        for record in self:
            record._get_journal_id()

    def _get_qr_apikey(self):
        company_id = self.company_id
        return company_id.sip_qr_prod_apikey if company_id.sip_environment == 'prod' else company_id.sip_qr_dev_apikey

    def _disable_sip_qr(self):
        self.env['account.move']._check_sip_auth_token(self.company_id)
        sip_url = self.company_id._get_sip_url()
        url = sip_url + '/api/v1/inhabilitarPago'
        headers = {
            'apikeyServicio': self._get_qr_apikey(),
            'Authorization': f'Bearer {self.company_id.sip_auth_token}',
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
                        self.env[self.source_model].sudo().search([('id', '=', self.source_res_id)]).sudo().write({'sip_qr_id': False})
                return response_data['mensaje']
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
                return response.text
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))
            return e

    def action_disable_sip_qr(self):
        for record in self:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Obtención token SIP",
                    "message": record._disable_sip_qr(),
                    "sticky": False,
                }
            }

    def _check_sip_state(self):
        self.env['account.move']._check_sip_auth_token(self.company_id)
        sip_url = self.company_id._get_sip_url()
        url = sip_url + '/api/v1/estadoTransaccion'
        headers = {
            'apikeyServicio': self._get_qr_apikey(),
            'Authorization': f'Bearer {self.company_id.sip_auth_token}',
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
                return response_data['mensaje']
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
                return response.text
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))
            return e

    def action_check_sip_state(self):
        for record in self:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Obtención token SIP",
                    "message": record._check_sip_state(),
                    "sticky": False,
                }
            }