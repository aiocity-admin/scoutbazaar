# -*- coding: utf-8 -*-

{
    'name': 'Theme Alan',
    'category': 'Theme/Ecommerce',
    'summary': 'Advanced eCommerce Responsive and Customizable Theme with 170+ Snippets.',
    'version': '3.23',
    'author': 'Atharva System',
    'sequence': 1000,
	'license' : 'OPL-1',
    'support': 'support@atharvasystem.com',
    'website' : 'https://www.atharvasystem.com',
    'description': """
Theme Alan is  is a Odoo theme with advanced ecommerce feature, extremely customizable and fully responsive. It's suitable for any e-commerce sites.
Start your Odoo store right away with The Alan theme.
Corporate theme,
Creative theme,
Ecommerce theme,
Education theme,
Entertainment theme,
Personal theme,
Services theme,
Technology theme,
Business theme,
Multipurpose odoo theme,
Multi-purpose theme,
        """,
    'depends': ['alan_customize','website_theme_install'],
    'data': [
        'views/customize_template.xml',
        'views/templates.xml',
        'data/theme_alan_data.xml',  
    ],
    'live_test_url': 'http://theme-alan.atharvasystem.com/',
	'images': ['static/description/alan_banner.png','static/description/alan_banner_screenshot.png'],
    'price': 149.00,
    'currency': 'EUR',
    'application': False,
}
