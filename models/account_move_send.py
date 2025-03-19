# -*- coding: utf-8 -*-

from odoo import models, api


class KyoheiSipApiMailTemplate(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_invoice_extra_attachments(self, move):
        return (
                super()._get_invoice_extra_attachments(move)
                + move.qr_attachment_id
        )
