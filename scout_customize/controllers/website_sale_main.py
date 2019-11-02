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
import json

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
    
    
    
    #Gift Product Code===============================
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST','GET'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))
        is_gift = False
        if not sale_order.order_line:
            if kw.get('order_line_email'):
                sale_order.with_context(is_gift = True,order_line_email=kw.get('order_line_email'))._cart_update(
                    product_id=int(product_id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    product_custom_attribute_values=product_custom_attribute_values,
                    no_variant_attribute_values=no_variant_attribute_values
                )
            else:
                sale_order._cart_update(
                    product_id=int(product_id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    product_custom_attribute_values=product_custom_attribute_values,
                    no_variant_attribute_values=no_variant_attribute_values
                )
        else:
            if kw.get('order_line_email'):
                sale_order.with_context(is_gift = True,order_line_email=kw.get('order_line_email'))._cart_update(
                    product_id=int(product_id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    product_custom_attribute_values=product_custom_attribute_values,
                    no_variant_attribute_values=no_variant_attribute_values
                    )
            else:
                sale_order._cart_update(
                    product_id=int(product_id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    product_custom_attribute_values=product_custom_attribute_values,
                    no_variant_attribute_values=no_variant_attribute_values
                    )
        return request.redirect("/shop/cart")

    #Check Gift Product======================================
    @http.route(['/check/gift'], type='json', auth="public", website=True,methods=['GET', 'POST'])
    def check_gift_product(self,p_id, **post):
        order = request.website.sale_get_order()
        p_id = request.env['product.product'].sudo().search([('id','=',int(p_id))])
        if p_id.product_tmpl_id:
            if p_id.product_tmpl_id.is_gift_product:
                return True
            else:
                return False
        else:
            return False

    #Check User exist or not in db for gift product======================================
    @http.route(['/check/user'], type='json', auth="public", website=True)
    def check_current_user(self, user_email, **post):
        if user_email:
            partner = request.env['res.users'].search([('partner_id.email','=',user_email)],limit=1)
            if partner:
                return True
            else:
                return False
            
            
    #Checkout Public User Redirect======================================
    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        
        order = request.website.sale_get_order()
        res = super(WebsiteSaleScout,self).checkout(**post)
        
        if request.env.user._is_public():
            return request.redirect('/web/login')
        else:
            return res
        
        
        
    #Prodcut Documents Download on website======================================
    @http.route(['/get/product_document'], type='json', auth="public", website=True)
    def product_document(self,product_id, **post):
        order = request.website.sale_get_order()
        attachment_links = {}
        product_attachment = request.env['ir.attachment'].search([('res_id','=',product_id),('res_model','=','product.product')])
        if product_attachment:
            for att in product_attachment:
                attachment_links.update({att.datas_fname : '/web/content/' + str(att.id) + '?download=true'})
            return attachment_links
        else:
            return False
        
        
        
    #Policies Page code==================================
    
    @http.route(['/shipping_policy'],type='http',auth="public",website=True)
    def company_shipping_policy(self):
        company =request.env.user.company_id
        return request.render('scout_customize.company_shipping_policy',{'company':company})
    
    @http.route(['/refund_policy'],type='http',auth="public",website=True)
    def company_refund_policy(self):
        company =request.env.user.company_id
        return request.render('scout_customize.company_refund_policy',{'company':company})
    
    
    @http.route(['/privacy'],type='http',auth="public",website=True)
    def company_privacy_policy(self):
        company =request.env.user.company_id
        return request.render('scout_customize.company_privacy_policy',{'company':company})
    
    
    @http.route(['/term_of_use'],type='http',auth="public",website=True)
    def company_term_of_use(self):
        company =request.env.user.company_id
        return request.render('scout_customize.company_term_of_use',{'company':company})
    
    
