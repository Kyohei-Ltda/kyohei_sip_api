# -*- coding: utf-8 -*-

import json

import requests
from odoo import models, fields
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class KyoheiBankIntegrationsSipClientMixin(models.AbstractModel):
    _name = 'sip.client.mixin'
    _description = 'Cliente SIP'

    def _get_sip_url(self):
        sip_url_param = 'sip_dev_url' if self.company_id.sip_environment == 'dev' else 'sip_prod_url'
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_bank_integrations.{sip_url_param}")
        return sip_url

    def _get_sip_callback(self):
        return f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/sip/confirmaPago" or ''

    def _get_sip_response(self, endpoint, server_method='get', header_dict=None, data_dict=None):
        if self.company_id.sip_auth_duration < datetime.now():
            self.company_id._get_sip_auth_token()
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
            return response
        except Exception as e:
            _logger.exception("Exception when getting SIP token: %s", str(e))
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Obtención token SIP",
                    "message": e,
                    "sticky": False,
                }
            }

    def _get_sip_token(self):
        self.company_id.action_get_sip_auth_token()

    sip_qr_id = fields.Many2one('sip.qr', string='QR SIP', copy=False, ondelete='set null')

    @staticmethod
    def _get_notification_action(operation, server_message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": operation,
                "message": server_message,
                "sticky": False,
            }
        }

    def _enable_sip_qr(self, data_dict):
        endpoint = '/api/v1/generaQr'
        header = {'Authorization': f'Bearer {self.company_id.sip_auth_token}'}
        sip_qr_enable_response = self._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        operation = 'Generar QR'
        if sip_qr_enable_response.status_code == 200:
            response_data = sip_qr_enable_response.json()
            currency_id = self.env['res.currency'].search([('name', '=', data_dict['moneda'])], limit=1)
            expiration_date = datetime.strptime(data_dict['fechaVencimiento'], '%d/%m/%Y').date()
            if response_data['codigo'] == '0000':
                sip_qr = json.loads(sip_qr_enable_response.content.decode('utf-8'))
                qr_id = self.env['sip.qr'].create({
                    'qr_image': sip_qr['objeto']['imagenQr'],
                    'ref': data_dict['alias'],
                    'label': data_dict['detalleGlosa'],
                    'amount': data_dict['monto'],
                    'currency_id': currency_id.id,
                    'date': expiration_date,
                    'for_single_use': data_dict['unicoUso'],
                    'company_id': self.company_id.id,
                    'ob_destination_account': sip_qr['objeto']['cuentaDestino'],
                    'state': 'pendiente'
                })
                self.write({'sip_qr_id': qr_id.id})
            return self._get_notification_action(operation, response_data['mensaje'])
        else:
            _logger.error("Failed to get SIP QR. Status code: %s, Response: %s", sip_qr_enable_response.status_code, sip_qr_enable_response.text)
            return self._get_notification_action(operation, sip_qr_enable_response.text)

    def _disable_sip_qr(self, data_dict):
        endpoint = '/api/v1/inhabilitarPago'
        header = {'Authorization': f'Bearer {self.company_id.sip_auth_token}'}
        sip_qr_disable_response = self._get_sip_response(
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
        operation = 'Deshabilitar QR'
        if sip_qr_disable_response.status_code == 200:
            response_data = sip_qr_disable_response.json()
            if response_data['codigo'] == '0000':
                self.sip_qr_id.write({'state': 'inhabilitado'})
                self.sip_qr_id = False
            return self._get_notification_action(operation, response_data['mensaje'])
        else:
            _logger.error("Failed to disable SIP QR. Status code: %s, Response: %s", sip_qr_disable_response.status_code, sip_qr_disable_response.text)
            return self._get_notification_action(operation, sip_qr_disable_response.text)


