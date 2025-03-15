# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import models, fields, api, exceptions


class KyoheiSipApiMove(models.Model):
    _name = 'account.move'
    _inherit = ['sip.client.mixin', 'account.move']

    def action_get_sip_qr(self):
        for record in self:
            record._set_payment_reference()
            qr_duration = record.company_id.sip_qr_duration
            qr_expiration_date = record.invoice_date_due  + timedelta(days=qr_duration)
            data_dict = {
                'alias': record.sip_reference,
                'callback': record._get_sip_callback(),
                'detalleGlosa': record.payment_reference,
                'monto': record.amount_residual,
                'moneda': record.currency_id.name,
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

    def _post(self, soft=True):
        record = super()._post(soft)
        sip_payment_provider = self.env['payment.provider'].search(
            [
                ('code', '=', 'sip'),
                ('state', 'in', ['test', 'enabled'])
            ], limit=1
        )
        for move in self:
            if move.country_code == 'BO':

                if sip_payment_provider:
                    record.action_get_sip_qr()
        return record

    def button_draft(self):
        record = super().button_draft()
        for move in self:
            if move.sip_qr_id and move.sip_qr_id.state == 'pendiente':
                move.sip_qr_id._disable_sip_qr()
        return record