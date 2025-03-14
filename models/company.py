# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class KyoheiSipApiCompany(models.Model):
    _inherit = 'res.company'

    sip_environment = fields.Selection(
        [('dev', 'Pruebas'),
         ('prod', 'Producción')],
        string='Entorno SIP',
        default='dev'
    )
    sip_username = fields.Char(string="Sip Username")
    sip_password = fields.Char(string="Sip Password")
    sip_auth_apikey = fields.Char(string="Sip Auth apikey")
    sip_qr_dev_apikey = fields.Char(string="Sip Qr Dev apikey")
    sip_qr_prod_apikey = fields.Char(string="Sip Qr Prod apikey")
    sip_auth_token = fields.Char(string='Autorización SIP')
    sip_auth_duration = fields.Datetime(string='SIP Auth Duration')

    sip_qr_duration = fields.Integer(string='Duración', default=7)
