# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import Response, request


class KyoheiBankIntegrationsControllers(http.Controller):
    @http.route('/endpoint/confirmaPago', type='http', csrf=False, auth="public", methods=['POST'])
    def confirm_sip_qr_payment(self):
        return Response(
            '{"codigo": "0000", "mensaje":"Registro exitoso"}',
            content_type='application/json;charset=utf-8',
            status=200
        )
