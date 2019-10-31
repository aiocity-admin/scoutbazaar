# -*- coding: utf-8 -*-

{
    'name': 'Paymaya Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Paymaya Implementation',
    'version': '12.0.0.1',
    'description': """Paymaya Payment Acquirer""",
    'depends': ['payment','sale'],
    'data': [
        'views/payment_views.xml',
        'views/payment_paymaya_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}