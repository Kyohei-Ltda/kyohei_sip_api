# -*- coding: utf-8 -*-

import json

import requests
from odoo import models, fields
from openpyxl.pivot import record


class KyoheiBankIntegrationsSipClientMixin(models.AbstractModel):
    _name = 'sip.client.mixin'
    _description = 'Cliente SIP'

    sip_auth_token = fields.Text(string='SIP Auth Token')
    sip_auth_duration = fields.Datetime(string='SIP Auth Duration')

    def _get_sip_url(self):
        if self.company_id.sip_environment == 'prod':
            sip_url = self.env['ir.config_parameter'].sudo().get_param("kyohei_bank_integrations.sip_dev_url")
        else:
            sip_url = self.env['ir.config_parameter'].sudo().get_param("kyohei_bank_integrations.sip_prod_url")
        return sip_url

    def _get_sip_apikey(self):
        return self.env['ir.config_parameter'].sudo().get_param("kyohei_service_client.sip_api_key") or ''

    def _get_sip_username(self):
        return self.env['ir.config_parameter'].sudo().get_param("kyohei_service_client.sip_username") or ''

    def _get_sip_password(self):
        return self.env['ir.config_parameter'].sudo().get_param("kyohei_service_client.sip_password") or ''

    def _get_sip_callback(self):
        return f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/endpoint/confirmaPago" or ''

    def _get_sip_response(self, endpoint, server_method='get', header_dict=None, data_dict=None):
        url = self._get_sip_url() + endpoint
        headers = {'apikey': self._get_sip_apikey()}
        if header_dict is not None:
            headers.update(header_dict)
        http_method = getattr(requests, server_method.lower())
        server_response = http_method(
            url=url,
            headers=headers,
            data=data_dict
        )
        return server_response

    def _get_sip_token(self):
        for record in self:
            endpoint = '/autenticacion/v1/generarToken'
            data = {
                'password': record._get_sip_password(),
                'username': record._get_sip_username(),
            }
            sip_token_response = record._get_sip_response(endpoint=endpoint, server_method='post', data_dict=data)
            if sip_token_response.status_code == 200:
                sip_token = json.loads(sip_token_response.content.decode('utf-8'))

    def _enable_sip_qr(self, auth_token, data_dict):
        for record in self:
            endpoint = '/autenticacion/v1/generaQr'
            header = {'Authorization': auth_token}
            sip_qr_enable_response = record._get_sip_response(
                endpoint=endpoint,
                server_method='post',
                header_dict=header,
                data_dict=data_dict
            )
            if sip_qr_enable_response.status_code == 200:
                sip_qr = json.loads(sip_qr_enable_response.content.decode('utf-8'))

    def _disable_sip_qr(self, data_dict):
        endpoint = '/autenticacion/v1/inhabilitarPago'
        header = {'Authorization': record.sip_auth_token}
        sip_qr_disable_response = record._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        if sip_qr_disable_response.status_code == 200:
            sip_qr = json.loads(sip_qr_disable_response.content.decode('utf-8'))

    def _check_sip_state(self, data_dict):
        endpoint = '/autenticacion/v1/estadoTransaccion'
        header = {'Authorization': record.sip_auth_token}
        sip_qr_disable_response = record._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        if sip_qr_disable_response.status_code == 200:
            sip_qr = json.loads(sip_qr_disable_response.content.decode('utf-8'))


