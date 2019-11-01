# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class ScoutProgram(models.Model):
    
    _name='scout.program'

    
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")