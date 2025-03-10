# -*- coding: utf-8 -*-

from odoo import _, fields, models


class KyoheiBankIntegrationsConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sip_environment = fields.Selection(related="company_id.sip_environment", readonly=False)
    sip_dev_url = fields.Char("Sip Dev URL", config_parameter="kyohei_bank_integrations.sip_dev_url", default="https://dev-sip.mc4.com.bo:8443")
    sip_prod_url = fields.Char("Sip Prod URL", config_parameter="kyohei_bank_integrations.sip_prod_url")

    sip_username = fields.Char(related="company_id.sip_username", readonly=False)
    sip_password = fields.Char(related="company_id.sip_password", readonly=False)

    sip_auth_apikey = fields.Char(related="company_id.sip_auth_apikey", readonly=False)
    sip_auth_token = fields.Text(related="company_id.sip_auth_token", readonly=False)
    sip_auth_duration = fields.Datetime(related="company_id.sip_auth_duration", readonly=False)

    sip_qr_apikey = fields.Char(related="company_id.sip_qr_apikey", readonly=False)
