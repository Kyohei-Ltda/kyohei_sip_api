# -*- coding: utf-8 -*-

import json

import requests
from odoo import models, fields
from openpyxl.pivot import record
import logging

_logger = logging.getLogger(__name__)


class KyoheiBankIntegrationsSipClientMixin(models.AbstractModel):
    _name = 'sip.client.mixin'
    _description = 'Cliente SIP'

    def _get_sip_url(self):
        sip_url_param = 'sip_dev_url' if self.company_id.sip_environment == 'dev' else 'sip_prod_url'
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_bank_integrations.{sip_url_param}")
        return sip_url

    def _get_sip_callback(self):
        return f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/endpoint/confirmaPago" or ''

    def _get_sip_response(self, endpoint, server_method='get', header_dict=None, data_dict=None):
        url = self._get_sip_url() + endpoint
        headers = {
            'apikeyServicio': self.company_id.sip_qr_apikey,
            'Content-Type': 'application/json'
        }
        if header_dict is not None:
            headers.update(header_dict)
        http_method = getattr(requests, server_method.lower())
        try:
            response = http_method(url=url, headers=headers, json=data_dict)
            _logger.info("SIP Token request status: %s", response.status_code)
            _logger.info("Response: %s", response.text)
            if response.status_code == 200:
                return response
            else:
                _logger.error("Failed to get SIP token. Status code: %s, Response: %s", response.status_code, response.text)
                return None
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))
            return None

    def _get_sip_token(self):
        self.company_id.action_get_sip_auth_token()

    sip_qr_image = fields.Binary(string='QR SIP', copy=False)

    def _enable_sip_qr(self, auth_token, data_dict):
        endpoint = '/api/v1/generaQr'
        header = {'Authorization': f'Bearer {auth_token}'}
        sip_qr_enable_response = self._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        if sip_qr_enable_response:
            sip_qr = json.loads(sip_qr_enable_response.content.decode('utf-8'))['objeto']['imagenQr']
            self.sip_qr_image = sip_qr

    def _disable_sip_qr(self, auth_token, data_dict):
        endpoint = '/api/v1/inhabilitarPago'
        header = {'Authorization': f'Bearer {auth_token}'}
        sip_qr_disable_response = self._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        if sip_qr_disable_response:
            self.sip_qr_image = False

    def _check_sip_state(self, auth_token, data_dict):
        endpoint = '/api/v1/estadoTransaccion'
        header = {'Authorization': f'Bearer {auth_token}'}
        sip_qr_check_response = self._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        if sip_qr_check_response:
            sip_qr = json.loads(sip_qr_check_response.content.decode('utf-8'))


