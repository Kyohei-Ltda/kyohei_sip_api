# -*- coding: utf-8 -*-

import json

import requests
from odoo import models, fields, exceptions
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

    @staticmethod
    def _check_sip_auth_token(company):
        reason_list = []
        if not company.sip_username:
            reason_list.append('Falta el "Usuario".')
        if not company.sip_password:
            reason_list.append('Falta la "Contraseña".')
        if not company.sip_auth_apikey:
            reason_list.append('Falta el "Auth Apikey".')
        if company.sip_environment == 'dev' and not company.sip_qr_dev_apikey or company.sip_environment == 'prod' and not company.sip_qr_prod_apikey:
            reason_list.append('Falta el "QR Apikey".')
        if len(reason_list) > 0:
            message_body = ''
            for index, reason in enumerate(reason_list):
                if index == 0:
                    message_body += '-' + reason
                else:
                    message_body += ('\n' + '-' + reason)
            raise exceptions.ValidationError(f'Fallas de configuración API SIP:\n{message_body}')
        else:
            if not company.sip_auth_duration or company.sip_auth_duration < datetime.now():
                company._get_sip_auth_token()

    def _get_sip_response(self, endpoint, server_method='get', header_dict=None, data_dict=None):
        company_id = self.company_id
        self._check_sip_auth_token(company_id)
        url = self._get_sip_url() + endpoint
        qr_apikey = company_id.sip_qr_prod_apikey if company_id.sip_environment == 'prod' else company_id.sip_qr_dev_apikey
        headers = {
            'apikeyServicio': qr_apikey,
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

    sip_qr_id = fields.Many2one('sip.qr', string='QR SIP', copy=False, ondelete='set null')

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
                    'partner_id': self.partner_id.id or False,
                    'qr_image': sip_qr['objeto']['imagenQr'],
                    'ref': data_dict['alias'],
                    'label': data_dict['detalleGlosa'],
                    'amount': data_dict['monto'],
                    'currency_id': currency_id.id,
                    'date': expiration_date,
                    'for_single_use': data_dict['unicoUso'],
                    'company_id': self.company_id.id,
                    'obfuscated_account': sip_qr['objeto']['cuentaDestino'],
                    'state': 'pendiente',
                    'source_model': self._name,
                    'source_res_id': self.id
                })
                qr_id._get_journal_id()
                self.write({'sip_qr_id': qr_id.id})
            return self._get_notification_action(operation, response_data['mensaje'])
        else:
            _logger.error("Failed to get SIP QR. Status code: %s, Response: %s", sip_qr_enable_response.status_code, sip_qr_enable_response.text)
            return self._get_notification_action(operation, sip_qr_enable_response.text)




