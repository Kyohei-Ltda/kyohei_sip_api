# -*- coding: utf-8 -*-
# from odoo import http


# class KyoheiBankIntegrations(http.Controller):
#     @http.route('/kyohei_bank_integrations/kyohei_bank_integrations', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kyohei_bank_integrations/kyohei_bank_integrations/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kyohei_bank_integrations.listing', {
#             'root': '/kyohei_bank_integrations/kyohei_bank_integrations',
#             'objects': http.request.env['kyohei_bank_integrations.kyohei_bank_integrations'].search([]),
#         })

#     @http.route('/kyohei_bank_integrations/kyohei_bank_integrations/objects/<model("kyohei_bank_integrations.kyohei_bank_integrations"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kyohei_bank_integrations.object', {
#             'object': obj
#         })

