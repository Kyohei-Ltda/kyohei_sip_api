# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from datetime import timedelta
import uuid


class KyoheiBankIntegrationsMove(models.Model):
    _name = 'account.move'
    _inherit = ['sip.client.mixin', 'account.move']

    def action_get_sip_qr(self):
        for record in self:
            payment_ref = str(uuid.uuid4())
            qr_expiration_date = record.invoice_date_due  + timedelta(days=1) if record.invoice_date_due < fields.Date.context_today(self) else fields.Date.context_today(self)
            self.payment_reference = payment_ref
            data_dict = {
                'alias': payment_ref,
                'callback': record._get_sip_callback(),
                'detalleGlosa': record.name,
                'monto': record.amount_residual,
                'moneda': record.currency_id.name,
                'fechaVencimiento': qr_expiration_date.strftime('%d/%m/%Y'),
                'tipoSolicitud': 'API',
                'unicoUso': True,
            }
            return record._enable_sip_qr(data_dict)

    def action_revoke_sip_qr(self):
        for record in self:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Obtención token SIP",
                    "message": record.sip_qr_id._disable_sip_qr(),
                    "sticky": False,
                }
            }

    def action_check_sip_payment(self):
        for record in self:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Obtención token SIP",
                    "message": record.sip_qr_id._check_sip_state(),
                    "sticky": False,
                }
            }
