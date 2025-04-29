# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import models, fields


class KyoheiSipApiProviderSelectorWizard(models.Model):
    _name = 'sip.payment.provider.selector.wizard'
    _description = 'Atualizador de divisas'

    move_id = fields.Many2one('account.move')
    payment_provider_id = fields.Many2one('payment.provider', string='Método de pago', domain=[('code', '=', 'sip')])

    def action_create_sip_qr(self):
        for record in self:
            invoice_id = record.move_id
            invoice_id._set_payment_reference()
            payment_provider_id = self.payment_provider_id
            qr_duration = payment_provider_id.sip_qr_duration
            qr_expiration_date = invoice_id.invoice_date_due + timedelta(days=qr_duration)
            residual_amount = invoice_id.amount_residual if invoice_id.currency_id == self.env.ref('base.BOB') else round(invoice_id.amount_residual * invoice_id._get_currency_rate(invoice_id.invoice_date), 2)
            data_dict = {
                'alias': invoice_id.sip_reference,
                'callback': invoice_id._get_sip_callback(),
                'detalleGlosa': invoice_id.payment_reference,
                'monto': residual_amount,
                'moneda': self.env.ref('base.BOB').name,
                'fechaVencimiento': qr_expiration_date.strftime('%d/%m/%Y'),
                'tipoSolicitud': 'API',
                'unicoUso': True,
            }
            invoice_id._enable_sip_qr(data_dict, payment_provider_id)