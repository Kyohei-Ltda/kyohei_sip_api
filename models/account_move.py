# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import models, fields, api, exceptions


class KyoheiSipApiMove(models.Model):
    _name = 'account.move'
    _inherit = ['sip.client.mixin', 'account.move']

    def action_get_sip_qr(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sip.payment.provider.selector.wizard',
            'view_id': self.env.ref('kyohei_sip_api.kyohei_payment_provider_selector_wizard_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_move_id': self.id
            }
        }

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