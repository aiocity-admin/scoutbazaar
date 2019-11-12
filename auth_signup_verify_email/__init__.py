# Copyright 2015 Antiun Ingeniería, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import controllers

import odoo 
from odoo import SUPERUSER_ID
from odoo import api

def post_init_hook(cr, registry):
	env = api.Environment(cr, odoo.SUPERUSER_ID, {})
	cr.execute("""
                update ir_model_data set noupdate=False where
                model ='mail.template' """)
