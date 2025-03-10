# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class KyoheiBankIntegrationsSipQr(models.Model):
    _name = 'sip.qr'
    _description = 'SIP QR'

    # Source
    ref = fields.Char()
    callback = fields.Char()
    label = fields.Char()
    amount = fields.Float()
    currency_id = fields.Char()
    date = fields.Date()
    for_single_use = fields.Boolean()