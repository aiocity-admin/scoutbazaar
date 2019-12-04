# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    shipping_charge = fields.Float(' Shipping Charge')
    
    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.sale_line_id.delivery_method:
            vals['carrier_id'] = self.sale_line_id.delivery_method.id
        return vals
    
class StockPicking_Charge(models.Model):
    _inherit = 'stock.picking'
    
    shipping_charge = fields.Float('Shipping Charge ', compute='_compute_shipping_charge')
    
    @api.multi
    @api.depends('sale_id')
    def _compute_shipping_charge(self):
        if self.sale_id:
            for line in self.sale_id.order_line:
                if line.location_id == self.location_id:
                    if line.shipping_charge:
                        self.shipping_charge += line.shipping_charge
