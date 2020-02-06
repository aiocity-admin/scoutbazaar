# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json


class WebsiteSale(WebsiteSale):
    
#     # inherit controoler to add quantity direct to press add to cart button from product listing
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST','GET'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        if not 'order_line_email' in kw:
            if add_qty:
                if int(add_qty) == 1:
                    product = request.env['product.product'].sudo().search([('id', '=', int(product_id))])
                    if product.sh_increment_qty != int(add_qty):
                        add_qty = product.sh_increment_qty
        res = super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)
        return res
    
class WebsiteSaleMain(WebsiteSale):
    
    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        if add_qty:
            if int(add_qty) == 1:
                product = request.env['product.product'].sudo().search([('id', '=', int(product_id))])
                if product.sh_increment_qty != int(add_qty):
                    add_qty = product.sh_increment_qty
        res = super(WebsiteSale, self).cart_update_json(product_id,line_id, add_qty, set_qty, display)
        return res