# -*- coding: utf-8 -*-
{
    'name': 'Student',
	'version': '12.0.1.0.0',
	'summary': 'Record Student Information',
	'category': 'Tools',
	'author': 'Niyas Raphy',
	'maintainer': 'Cybrosys Techno Solutions',
	'company': 'Cybrosys Techno Solutions',
	'website': 'https://www.cybrosys.com',
	'depends': ['base','website'],
	'data': [
        'security/ir.model.access.csv',
        'views/student_view.xml',
		'views/templates.xml'
	],
	'images': [],
	'license': 'AGPL-3',
	'installable': True,
	'application': False,
	'auto_install': False,
}