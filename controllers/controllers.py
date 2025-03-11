# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import Response, request


class KyoheiBankIntegrationsControllers(http.Controller):
    @http.route('/sip/confirmaPago', type='json', csrf=False, auth="public", methods=['POST'])
    def confirm_sip_qr_payment(self):
        data = request.httprequest.json
        payment_ref = data.get('alias')
        sip_qr_id = request.env['sip.qr'].sudo().search([('ref', '=', payment_ref)])
        if sip_qr_id:
            bank_statement_line_id = request.env['account.bank.statement.line'].sudo().search([('payment_ref', '=', payment_ref)])
            if not bank_statement_line_id:
                request.env['account.bank.statement.line'].sudo().create({
                    'date': data.get('fechaproceso')
                })
        return Response(
            '{"codigo": "0000", "mensaje":"Registro exitoso"}',
            content_type='application/json;charset=utf-8',
            status=200
        )
