# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from datetime import datetime


class KyoheiBankIntegrationsMove(models.Model):
    _name = 'account.move'
    _inherit = ['sip.client.mixin', 'account.move']

    def action_get_sip_qr(self):
        for record in self:
            data_dict = {
                'alias': record.name,
                'callback': record._get_sip_callback(),
                'detalleGlosa': record.invoice_line_ids[0].name,
                'monto': record.amount_residual,
                'moneda': record.currency_id.name,
                'fechaVencimiento': record.invoice_date_due,
                'tipoSolicitud': 'API',
                'unicoUso': True,
            }
            record._enable_sip_qr(
                record.company_id.sip_auth_token,
                data_dict
            )

    def action_revoke_sip_qr(self):
        for record in self:
            data_dict = {'alias': record.name}
            record._disable_sip_qr()

    def action_check_sip_payment(self):
        for record in self:
            data_dict = {'alias': record.name}
            record._check_sip_state()
