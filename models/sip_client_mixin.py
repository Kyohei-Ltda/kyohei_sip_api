# -*- coding: utf-8 -*-

import json
import logging
import uuid
from datetime import datetime

import requests
from odoo import models, fields, exceptions

_logger = logging.getLogger(__name__)


class KyoheiSipApiSipClientMixin(models.AbstractModel):
    _name = 'sip.client.mixin'
    _description = 'Cliente SIP'

    def _get_currency_rate(self, date):
        date_search = date if date else fields.Date.context_today(self)
        try:
            currency_rate = self.env['res.currency.rate'].search(['&', ['currency_id', '=', self.currency_id.id], ['name', '<=', date_search]], order='name desc', limit=1)[0].inverse_company_rate
        except IndexError:
            _logger.exception(f"No exchange rate set for {self.currency_id.name}")
            currency_rate = 0
        return currency_rate

    def _get_sip_url(self, payment_provider):
        sip_url_param = 'sip_prod_url' if payment_provider.state == 'enabled' else 'sip_dev_url'
        sip_url = self.env['ir.config_parameter'].sudo().get_param(f"kyohei_sip_api.{sip_url_param}")
        return sip_url

    def _get_sip_callback(self):
        return f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/sip/confirmaPago" or ''

    def _get_sip_token(self):
        self.env['payment.provider'].search([('code', '=', 'sip')], limit=1)._get_sip_auth_token()

    def _check_sip_auth_token(self, payment_provider):
        reason_list = []
        if not payment_provider.sip_dev_username and payment_provider.state == 'test' or not payment_provider.sip_prod_username and payment_provider.state == 'enabled':
            reason_list.append('Falta el "Usuario".')
        if not payment_provider.sip_dev_password and payment_provider.state == 'test' or not payment_provider.sip_prod_password and payment_provider.state == 'enabled':
            reason_list.append('Falta la "Contraseña".')
        if not payment_provider.sip_dev_auth_apikey and payment_provider.state == 'test' or not payment_provider.sip_prod_auth_apikey and payment_provider.state == 'enabled':
            reason_list.append('Falta el "Auth Apikey".')
        if not payment_provider.sip_qr_dev_apikey and payment_provider.state == 'test' or not payment_provider.sip_qr_prod_apikey and payment_provider.state == 'enabled':
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
            if not payment_provider.sip_auth_duration or payment_provider.sip_auth_duration < datetime.now():
                self._get_sip_token()

    def _get_sip_response(self, payment_provider, endpoint, server_method='get', header_dict=None, data_dict=None):
        self._check_sip_auth_token(payment_provider)
        url = self._get_sip_url(payment_provider) + endpoint
        qr_apikey = payment_provider.sip_qr_prod_apikey if payment_provider.state == 'enabled' else payment_provider.sip_qr_dev_apikey
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

    sip_qr_id = fields.Many2one('sip.qr', string='QR SIP', copy=False, ondelete='set null')
    qr_attachment_id = fields.Many2one('ir.attachment')
    sip_reference = fields.Char(string='Referencia SIP', copy=False)

    def _set_payment_reference(self):
        self.sip_reference = str(uuid.uuid4())

    def _enable_sip_qr(self, data_dict, payment_provider):
        endpoint = '/api/v1/generaQr'
        header = {'Authorization': f'Bearer {payment_provider.sip_auth_token}'}
        sip_qr_enable_response = self._get_sip_response(
            payment_provider=payment_provider,
            endpoint=endpoint,
            server_method='post',
            header_dict=header,
            data_dict=data_dict
        )
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
                    'obfuscated_account': sip_qr['objeto']['cuentaDestino'],
                    'state': 'pendiente',
                    'source_model': self._name,
                    'source_res_id': self.id,
                    'payment_provider_id': payment_provider.id
                })

                # Create attachment
                qr_attachment = self.env['ir.attachment'].create({
                    'datas': qr_id.qr_image,
                    'name': 'QR Pago',
                    'mimetype': 'image/png',
                    'res_model': self._name,
                    'res_id': self.id,
                })

                self.write({
                    'sip_qr_id': qr_id.id,
                    'qr_attachment_id': qr_attachment
                })
        else:
            _logger.error("Failed to get SIP QR. Status code: %s, Response: %s", sip_qr_enable_response.status_code, sip_qr_enable_response.text)




