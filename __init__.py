# -*- coding: utf-8 -*-

from odoo.addons.payment import setup_provider, reset_payment_provider

from . import controllers
from . import wizards
from . import models


def kyohei_sip_api_post_init_hook(env):
    setup_provider(env, 'sip')
    env['ir.config_parameter'].sudo().create({'key': 'kyohei_sip_api.sip_dev_url', 'value': 'https://dev-sip.mc4.com.bo:8443'})
    env['ir.config_parameter'].sudo().create({'key': 'kyohei_sip_api.sip_prod_url', 'value': 'https://sip.mc4.com.bo:8443'})

def kyohei_sip_api_uninstall_hook(env):
    reset_payment_provider(env, 'sip')
    sip_dev_url_parameter = env['ir.config_parameter'].search([['key', '=', 'kyohei_sip_api.sip_dev_url']])
    if sip_dev_url_parameter:
        sip_dev_url_parameter.sudo().unlink()
    sip_prod_url_parameter = env['ir.config_parameter'].search([['key', '=', 'kyohei_sip_api.sip_prod_url']])
    if sip_prod_url_parameter:
        sip_prod_url_parameter.sudo().unlink()
