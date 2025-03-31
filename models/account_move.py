# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import models, fields, api, exceptions


class KyoheiSipApiMove(models.Model):
    _name = 'account.move'
    _inherit = ['sip.client.mixin', 'account.move']

    def action_get_sip_qr(self):
        for record in self:
            record._set_payment_reference()
            payment_provider_id = record._get_payment_provider()
            qr_duration = payment_provider_id.sip_qr_duration
            qr_expiration_date = record.invoice_date_due  + timedelta(days=qr_duration)
            residual_amount = record.amount_residual if self.currency_id == self.env.ref('base.BOB') else round(record.amount_residual * record._get_currency_rate(record.invoice_date), 2)
            data_dict = {
                'alias': record.sip_reference,
                'callback': record._get_sip_callback(),
                'detalleGlosa': record.payment_reference,
                'monto': residual_amount,
                'moneda': self.env.ref('base.BOB').name,
                'fechaVencimiento': qr_expiration_date.strftime('%d/%m/%Y'),
                'tipoSolicitud': 'API',
                'unicoUso': True,
            }
            return record._enable_sip_qr(data_dict)

    def action_revoke_sip_qr(self):
        for record in self:
            record.sip_qr_id._disable_sip_qr()

    def action_check_sip_payment(self):
        for record in self:
            record.sip_qr_id._check_sip_state()

    def button_draft(self):
        record = super().button_draft()
        for move in self:
            if move.sip_qr_id and move.sip_qr_id.state == 'pendiente':
                move.sip_qr_id._disable_sip_qr()
        return record