# -*- coding: utf-8 -*-
{
    'name': "Integraciones bancarias",

    'summary': """
    Integre su Odoo con las API de los bancos de Bolivia
    """,

    'description': """
Aproveche las integraciones de los bancos en Bolivia
================================================================================

Después de instalar el módulo obtendrá:
    * Generación de códigos QR para cobros por sus servicios
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
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ]
}
