# -*- coding: utf-8 -*-

import logging

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError
import uuid


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return SIP-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'sip':
            return res

        rendering_values = {
            'api_url': f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/payment/sip/process",
            'sip_alias': str(uuid.uuid4()),
        }
        return rendering_values
