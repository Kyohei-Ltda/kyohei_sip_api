# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta

import requests
from odoo import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class KyoheiSipApiCompany(models.Model):
    _inherit = 'res.company'

    sip_environment = fields.Selection(
        [('dev', 'Pruebas'),
         ('prod', 'Producción')],
        string='Entorno SIP',
        default='dev'
    )
    sip_username = fields.Char(string="Sip Username")
    sip_password = fields.Char(string="Sip Password")
    sip_auth_apikey = fields.Char(string="Sip Auth apikey")
    sip_qr_dev_apikey = fields.Char(string="Sip Qr Dev apikey")
    sip_qr_prod_apikey = fields.Char(string="Sip Qr Prod apikey")
    sip_auth_token = fields.Text(string='Autorización SIP')
    sip_auth_duration = fields.Datetime(string='SIP Auth Duration')

    def _get_sip_url(self):
        sip_url_param = 'sip_dev_url' if self.sip_environment == 'dev' else 'sip_prod_url'
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_sip_api.{sip_url_param}")
        return sip_url

    def _get_sip_auth_token(self):
        for record in self:
            url = record._get_sip_url() + '/autenticacion/v1/generarToken'
            headers = {
                'apikey': record.sip_auth_apikey,
                'Content-Type': 'application/json'
            }
            data = {
                'password': record.sip_password,
                'username': record.sip_username,
            }
            try:
                response = requests.post(url=url, headers=headers, json=data)
                response_data = response.json()
                _logger.info("SIP Token request status: %s", response.status_code)
                _logger.info("Response: %s", response.text)
                if response.status_code == 200:
                    if response_data['codigo'] == 'OK':
                        sip_token = response.json()['objeto']['token']
                        record.sip_auth_token = sip_token
                        record.sip_auth_duration = datetime.now() + timedelta(hours=4)
                        return response_data['mensaje']
                else:
                    _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
                    return response.text
            except Exception as e:
                _logger.exception("Exception when getting SIP token: %s", str(e))
                return e
