# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.osv.expression import expression

class StockReportInherit(models.Model):
    
    _inherit = 'stock.report'
    
    delivery_user_id = fields.Many2one('res.users', "Delivery User",related="picking_id.delivery_line_user" ,readonly=True)
    
    def _select(self):
        select_str = """
            sm.id as id,
            sp.name as picking_name,
            sp.date_done as date_done,
            sp.creation_date as creation_date,
            sp.scheduled_date as scheduled_date,
            sp.partner_id as partner_id,
            sp.is_backorder as is_backorder,
            sp.delay as delay,
            sp.delay > 0 as is_late,
            sp.cycle_time as cycle_time,
            spt.code as picking_type_code,
            spt.name as operation_type,
            p.id as product_id,
            sm.reference as reference,
            sm.picking_id as picking_id,
            sm.inventory_id as inventory_id,
            sm.state as state,
            sm.product_qty as product_qty,
            sm.company_id as company_id,
            cat.id as categ_id,
            sm.picking_id as delivery_user_id
        """
 
        return select_str
