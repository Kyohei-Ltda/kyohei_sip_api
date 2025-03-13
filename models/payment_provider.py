# -*- coding: utf-8 -*-

import hashlib
import logging
import requests

from odoo import fields, models, exceptions

from odoo.addons.payment_aps import const
from datetime import timedelta
from datetime import datetime


_logger = logging.getLogger(__name__)


class KyoheiSipApiPaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('sip', 'SIP')],
        ondelete={'sip': 'set default'},
        copy=False)
    sip_username = fields.Char(related='company_id.sip_username', readonly=False)
    sip_password = fields.Char(related='company_id.sip_password', readonly=False)
    sip_auth_apikey = fields.Char(related='company_id.sip_auth_apikey', readonly=False)
    sip_qr_dev_apikey = fields.Char(related='company_id.sip_qr_dev_apikey', readonly=False)
    sip_qr_prod_apikey = fields.Char(related='company_id.sip_qr_prod_apikey', readonly=False)
    sip_auth_token = fields.Text(related='company_id.sip_auth_token', readonly=False)
    sip_auth_duration = fields.Datetime(related='company_id.sip_auth_duration', readonly=False)

    def _get_sip_url(self):
        if self.state == 'enabled':
            sip_url_param = 'sip_prod_url'
        elif self.state == 'test':
            sip_url_param = 'sip_dev_url'
        else:
            raise exceptions.ValidationError('No puede solicitar token si no define un entorno.')
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_sip_api.{sip_url_param}")
        return sip_url

    def _get_sip_qr_apikey(self):
        if self.state == 'enabled':
            sip_qr_apikey = self.provider_id.sip_qr_prod_apikey
        elif self.state == 'test':
            sip_qr_apikey = self.provider_id.sip_qr_dev_apikey
        else:
            sip_qr_apikey = ''
        return sip_qr_apikey

    def _get_sip_auth_token(self):
        url = self._get_sip_url() + '/autenticacion/v1/generarToken'
        headers = {
            'apikey': self.sip_auth_apikey,
            'Content-Type': 'application/json'
        }
        data = {
            'password': self.sip_password,
            'username': self.sip_username,
        }
        try:
            response = requests.post(url=url, headers=headers, json=data)
            response_data = response.json()
            _logger.info("SIP Token request status: %s", response.status_code)
            _logger.info("Response: %s", response.text)
            if response.status_code == 200:
                if response_data['codigo'] == 'OK':
                    sip_token = response.json()['objeto']['token']
                    self.sip_auth_token = sip_token
                    self.sip_auth_duration = datetime.now() + timedelta(hours=4)
                    return response_data['mensaje']
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
                return response.text
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))
            return e
