# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class KyoheiBankIntegrationsCompany(models.Model):
    _name = 'res.company'
    _inherit = ['sip.client.mixin', 'res.company']

    sip_environment = fields.Selection(
        [('dev', 'Pruebas'),
         ('prod', 'Producción')],
        string='Entorno SIP',
        default='dev'
    )
    sip_username = fields.Char(string="Sip Username")
    sip_password = fields.Char(string="Sip Password")
    sip_api_key = fields.Char(string="Sip apikey")
    sip_auth_token = fields.Text(string='Autorización SIP')

    def action_get_sip_auth_token(self):
        for record in self:
            sip_token = record._get_sip_token()
            if sip_token:
                record.sip_auth_token = sip_token
