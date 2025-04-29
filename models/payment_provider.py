# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from datetime import timedelta

import requests
from odoo import fields, models, exceptions, api
from odoo.addons.payment_aps import const

_logger = logging.getLogger(__name__)


class KyoheiSipApiPaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('sip', 'SIP')],
        ondelete={'sip': 'set default'})

    sip_dev_username = fields.Char(string='Dev username')
    sip_prod_username = fields.Char(string='Prod username')
    sip_dev_password = fields.Char(string='Dev password')
    sip_prod_password = fields.Char(string='Prod password')
    sip_dev_auth_apikey = fields.Char(string='Dev auth apikey')
    sip_prod_auth_apikey = fields.Char(string='Prod auth apikey')
    sip_qr_dev_apikey = fields.Char(string='Dev QR apikey')
    sip_qr_prod_apikey = fields.Char(string='Prod QR apikey')
    sip_auth_token = fields.Char(string='Auth token')
    sip_auth_duration = fields.Datetime(string='Token Duration')
    sip_qr_duration = fields.Integer(string='QR Duration', default=1)
    sip_username = fields.Char(string='Callback username')
    sip_password = fields.Char(string='Callback password')

    def _get_sip_url(self):
        if self.state == 'enabled':
            sip_url_param = 'sip_prod_url'
        else:
            sip_url_param = 'sip_dev_url'
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_sip_api.{sip_url_param}")
        return sip_url

    def _get_sip_qr_apikey(self):
        if self.state == 'enabled':
            sip_qr_apikey = self.provider_id.sip_qr_prod_apikey
        else:
            sip_qr_apikey = self.provider_id.sip_qr_dev_apikey
        return sip_qr_apikey

    def _get_sip_auth_token(self):
        url = self._get_sip_url() + '/autenticacion/v1/generarToken'
        sip_auth_apikey = self.sip_prod_auth_apikey if self.state == 'enabled' else self.sip_dev_auth_apikey
        sip_username = self.sip_prod_username if self.state == 'enabled' else self.sip_dev_username
        sip_password = self.sip_prod_password if self.state == 'enabled' else self.sip_dev_password
        headers = {
            'apikey': sip_auth_apikey,
            'Content-Type': 'application/json'
        }
        data = {
            'password': sip_password,
            'username': sip_username,
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
                    _logger.info(f"Succes in getting SIP token: {response_data['mensaje']}")
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))
