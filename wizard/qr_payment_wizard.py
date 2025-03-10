# -*- coding: utf-8 -*-

from odoo import fields, models


class KyoheiBankIntegrationQrPaymentWizard(models.TransientModel):
    _name = 'qr.payment.wizard'
    _description = "Bolivian QR payment wizard"

    journal_id = fields.Many2one('account.journal')

