# -*- coding: utf-8 -*-


import json
import logging
import pprint
from datetime import datetime

import pytz
from odoo import http
from odoo.http import Response, request

_logger = logging.getLogger(__name__)


class KyoheiSipApiControllers(http.Controller):
    @http.route('/payment/sip/process', type='http', auth='public', methods=['POST'], csrf=False)
    def custom_process_transaction(self, **post):
        _logger.info("Handling custom processing with data:\n%s", pprint.pformat(post))
        return request.redirect('/payment/status')

    @http.route('/sip/confirmaPago', type='http', csrf=False, auth="public", methods=['POST'])
    def confirm_sip_qr_payment(self):
        data = request.httprequest.json
        sip_reference = data.get('alias')
        sip_qr_id = request.env['sip.qr'].sudo().search([('ref', '=', sip_reference)], limit=1)
        sip_qr_id.sudo().write({'state': 'pagado'})

        _logger.info("SIP notification: %s", str(data))
        if sip_qr_id:
            # Set payment transaction as done
            payment_transaction_id = request.env['payment.transaction'].sudo().search([('reference', '=',  sip_qr_id.label)], limit=1)
            if payment_transaction_id:
                payment_transaction_id.sudo()._set_done()
            # Check authentication
            auth = request.httprequest.authorization
            username = auth.username
            password = auth.password
            if username == sip_qr_id.payment_provider_id.sip_username and password == sip_qr_id.payment_provider_id.sip_password:
                # Create bank statement
                bank_statement_line_id = request.env['account.bank.statement.line'].sudo().search([('ref', '=', sip_qr_id.label)], limit=1)
                if not bank_statement_line_id:
                    timestamp_ms = data.get('fechaproceso', 0)
                    process_date = datetime.fromtimestamp(timestamp_ms / 1000.0)
                    la_paz_tz = pytz.timezone('America/La_Paz')
                    localized_process_date = pytz.utc.localize(process_date).astimezone(la_paz_tz) if timestamp_ms else datetime.now()
                    request.env['account.bank.statement.line'].sudo().create({
                        'ref': sip_qr_id.label,
                        'date': localized_process_date,
                        'journal_id': sip_qr_id.journal_id.id,
                        'currency_id': sip_qr_id.currency_id.id,
                        'payment_ref': f"Cobro automático QR SIP: {sip_reference}",
                        'amount': data.get('monto'),
                        'transaction_type': 'QR SIP'
                    })
            return Response(
                json.dumps({"codigo": "0000", "mensaje": "Registro exitoso"}),
                content_type='application/json;charset=utf-8',
                status=200
            )
        else:
            return Response(
                json.dumps({"codigo": "9999", "mensaje": "No existe el QR en la base de datos"}),
                content_type='application/json;charset=utf-8',
                status=500
            )
