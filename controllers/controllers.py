# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import Response, request
from datetime import datetime
import json


class KyoheiSipApiControllers(http.Controller):
    @http.route('/sip/confirmaPago', type='json', csrf=False, auth="public", methods=['POST'])
    def confirm_sip_qr_payment(self):
        data = request.httprequest.json
        payment_ref = data.get('alias')
        sip_qr_id = request.env['sip.qr'].sudo().search([('ref', '=', payment_ref)], limit=1)
        sip_qr_id.sudo().write({'state': 'pagado'})
        process_date_str = data.get('fechaproceso')
        if sip_qr_id:
            bank_statement_line_id = request.env['account.bank.statement.line'].sudo().search([('payment_ref', '=', payment_ref)])
            if not bank_statement_line_id:
                request.env['account.bank.statement.line'].sudo().create({
                    'date': datetime.strptime(process_date_str, "%b %d, %Y %I:%M:%S %p"),
                    'journal_id': sip_qr_id.journal_id.id,
                    'currency_id': sip_qr_id.currency_id.id,
                    'payment_ref': sip_qr_id.ref,
                    'partner_id': sip_qr_id.partner_id.id,
                    'ref': sip_qr_id.label,
                    'amount': data.get('monto'),
                    'transaction_type': 'QR SIP'
                })
            return Response(
                '{"codigo": "0000", "mensaje": "Registro exitoso"}',
                content_type='application/json;charset=utf-8',
                status=200
            )
        else:
            return Response(
                json.dumps({"codigo": "9999", "mensaje": "No existe el QR en la base de datos"}),
                content_type='application/json;charset=utf-8',
                status=500
            )
