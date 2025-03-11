# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import requests
import logging

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
         ('expirado', 'Expirado'),],
        string='Entorno SIP',
        default='dev'
    )
    qr_image = fields.Binary()
    ref = fields.Char(string='Alias')
    label = fields.Char(string='Detalle')
    amount = fields.Float(string='Monto')
    currency_id = fields.Many2one('res.currency', string='Divisa')
    date = fields.Date(string='Fecha vencimiento')
    for_single_use = fields.Boolean(string='Uso único')
    company_id = fields.Many2one('res.company', string='Company')
    journal_id = fields.Many2one('account.journal', string='Diario')
    ob_destination_account = fields.Char()

    def _get_journal_id(self):
        if self.ob_destination_account:
            pass

    def _check_sip_state(self):
        sip_url = self.company_id._get_sip_url()
        url = sip_url + '/api/v1/estadoTransaccion'
        headers = {
            'apikeyServicio': self.company_id.sip_qr_apikey,
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