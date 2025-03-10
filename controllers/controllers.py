# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import Response, request


class KyoheiBankIntegrationsControllers(http.Controller):
    @http.route('/endpoint/confirmaPago', type='http', csrf=False, auth="public", methods=['POST'])
    def confirm_sip_qr_payment(self):
        # data = request.jsonrequest
        # alias = data.get("alias")
        # numeroOrdenOriginante = data.get("numeroOrdenOriginante")
        # monto = data.get("monto")
        # idQr = data.get("idQr")
        # moneda = data.get("moneda")
        # fechaProceso = data.get("fechaProceso")
        # cuentaCliente = data.get("cuentaCliente")
        # nombreCliente = data.get("nombreCliente")
        # documentoCliente = data.get("documentoCliente")
        return Response(
            '{"codigo": "0000", "mensaje":"Registro exitoso"}',
            content_type='application/json;charset=utf-8',
            status=200
        )
