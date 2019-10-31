# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from datetime import datetime
from odoo import http, tools, _
from odoo import api, models, fields, _
import logging
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from werkzeug.exceptions import Forbidden
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale.controllers.main import QueryURL

class WebsiteSaleScout(WebsiteSale):
    
    
        #Storefront Shop Filters======================================
        def toggle_views(self):
        
            xml_ids = ['alan_customize.collapsible_filters','alan_customize.clear_attribute_filter','website_sale.products_attributes','alan_customize.average_rating','alan_customize.product_comment','alan_customize.product_filter_title']
            ir_ui_view_ids = request.env['ir.ui.view'].sudo().search([('key','in',xml_ids),('active','=',False)])
             
            if ir_ui_view_ids:
                for view_id in ir_ui_view_ids:
                    view_id.toggle()
                    
        
        
        @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
        '''/shop/brand/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand>''',
        '''/shop/brand/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand>/page/<int:page>''',
        ], type='http', auth="public", website=True)
        def shop(self, page=0, category=None, search='',ppg=False,brand=None, **post):
            res = super(WebsiteSaleScout, self).shop(
                    page, category, search, ppg, **post)
            
            
            self.toggle_views()
            
            return res