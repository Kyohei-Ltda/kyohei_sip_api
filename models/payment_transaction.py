# -*- coding: utf-8 -*-

import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _name = 'payment.transaction'
    _inherit = ['sip.client.mixin', 'payment.transaction']

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

        # SIP QR generation

        if not self.sip_qr_id:
            self._set_payment_reference()
            current_date = self.last_state_change.date()
            amount = self.amount if self.currency_id == self.env.ref('base.BOB') else self.amount * self._get_currency_rate(current_date)
            data_dict = {
                'alias': self.sip_reference,
                'callback': self._get_sip_callback(),
                'detalleGlosa': self.reference,
                'monto': amount,
                'moneda': self.env.ref('base.BOB').name,
                'fechaVencimiento': current_date.strftime('%d/%m/%Y'),
                'tipoSolicitud': 'API',
                'unicoUso': True,
            }
            self._enable_sip_qr(data_dict)
            if not self.sip_qr_id:
                raise ValidationError(
                    "Pago SIP: " + _("No se pudo generar el QR inténtelo más tarde.")
                )
        rendering_values = {
            'api_url': f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/payment/sip/process",
        }
        return rendering_values
