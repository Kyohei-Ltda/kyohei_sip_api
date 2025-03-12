# -*- coding: utf-8 -*-
{
    'name': "Integración SIP",

    'summary': """
    Integre su Odoo con las API SIP para cobros QR
    """,

    'description': """
Aproveche las integraciones con SIP para sus cobros
================================================================================

Después de instalar el módulo obtendrá:
    * Generación de códigos QR para cobros
    * Extractos bancarios automáticamente conciliados
    """,
    'author': "Kyohei Ltda.",
    'website': "https://localizacion.kyohei.bo/",
    'category': 'Accounting/Localizations',
    'countries': ['bo'],
    'version': '18.0.0.1',
    'depends': ['account'],
    'license': 'Other proprietary',
    'data': [
        'data/reconcile_model.xml',
        'data/sequence_data.xml',
        'data/server_action_data.xml',
        'security/ir.model.access.csv',
        'settings/settings_view.xml',
        'views/account_move_view.xml',
        'views/sip_qr_view.xml',
    ]
}
