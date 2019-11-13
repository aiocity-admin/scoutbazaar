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
    
#     delete address code=================
    @http.route(['/my/delete/address'], type='json', auth="public")
    def DeleteAddress(self, **kw):
        if 'deleteaddress' in kw:
            partner = kw.get("deleteaddress", False)
            partner_address = request.env['res.partner'].sudo().search([('id','=',int(partner))],limit=1)
            if partner_address:
                sale_order_shipping = request.env['sale.order'].sudo().search([('partner_shipping_id','=',partner_address.id)])
                sale_order_billing = request.env['sale.order'].sudo().search([('partner_id','=',partner_address.id)])
                shipping_len = len(sale_order_shipping)
                billing_len = len(sale_order_billing)
                if shipping_len == 0 and billing_len == 0:
                    partner_address.unlink()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    
    #Storefront Shop Filters======================================
    def toggle_views(self):
    
        xml_ids = ['alan_customize.collapsible_filters','alan_customize.clear_attribute_filter','website_sale.products_attributes','alan_customize.average_rating','alan_customize.product_comment','alan_customize.product_filter_title']
        ir_ui_view_ids = request.env['ir.ui.view'].sudo().search([('key','in',xml_ids),('active','=',False)])
         
        if ir_ui_view_ids:
            for view_id in ir_ui_view_ids:
                view_id.toggle()
                
    #Return Category Filter===============================
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
        if category:
            request.session['my_current_category'] = category.id
        
        if not category:
            keep = res.qcontext.get('keep')
            if 'my_current_category' in request.session:
                if request.session['my_current_category']:
                    sc_active_id = int(request.session['my_current_category'])
                    current_sc_id = request.env['product.public.category'].sudo().search([('id','=',int(sc_active_id))],limit=1)
                    if current_sc_id:
                        return request.redirect(keep('/shop/category/%s' % slug(current_sc_id),category=0))
                    else:
                        return request.render('scout_customize.not_category_msg')


        # //rajesh 4 nov

        if not request.env.user._is_public():
            partner = request.env.user.partner_id
            
            if category:
                school_ids = request.env['product.template'].sudo().search([('school_list_ids','in', partner.school_list_ids.ids),('public_categ_ids','=',category.id)])
                school_ids_not = request.env['product.template'].sudo().search([('school_list_ids','=', False),('public_categ_ids','=',category.id)])
                products = school_ids + school_ids_not
                if products and not request.env.user._is_public():
                    partner = request.env.user.partner_id
                    restricted_products = []
                    products_new = False
                    if partner.school_list_ids:
                        products_order_by = request.env['product.template'].search([('school_list_ids','in',partner.school_list_ids.ids)])
                        if products_order_by and school_ids:
                            product_new_list = []
                            product_old_list = []
                            for product in products:
                                if product in products_order_by:
                                    product_new_list.append(product.id)
                                else:
                                    product_old_list.append(product.id)
                            products_new = request.env['product.template'].browse(product_new_list)
                            products_new |= request.env['product.template'].browse(product_old_list)
                            if ppg:
                                try:
                                    ppg = int(ppg)
                                except ValueError:
                                    ppg = PPG
                                post["ppg"] = ppg
                            else:
                                ppg = PPG
                                
                        else:
                            products_new = products
                            
                    else:
                        products_new = products
                            
                    if restricted_products:
                        products_new = products_new.filtered(lambda p:p.id not in restricted_products)
                    
                # else:
                #     return False    

            else:
                school_ids = request.env['product.template'].sudo().search([('school_list_ids','in', partner.school_list_ids.ids)])
                school_ids_not = request.env['product.template'].sudo().search([('school_list_ids','=', False)])
                products = school_ids + school_ids_not
                if products and not request.env.user._is_public():
                    partner = request.env.user.partner_id
                    restricted_products = []
                    products_new = False
                    if partner.school_list_ids:
                        products_order_by = request.env['product.template'].search([('school_list_ids','in',partner.school_list_ids.ids)])
                        if products_order_by and school_ids:
                            product_new_list = []
                            product_old_list = []
                            for product in products:
                                if product in products_order_by:
                                    product_new_list.append(product.id)
                                else:
                                    product_old_list.append(product.id)
                            products_new = request.env['product.template'].browse(product_new_list)
                            products_new |= request.env['product.template'].browse(product_old_list)
                            if ppg:
                                try:
                                    ppg = int(ppg)
                                except ValueError:
                                    ppg = PPG
                                post["ppg"] = ppg
                            else:
                                ppg = PPG
                                
                        else:
                            products_new = products
                            
                    else:
                        products_new = products
                            
                    if restricted_products:
                        products_new = products_new.filtered(lambda p:p.id not in restricted_products)

                    res.qcontext.update({
                                 'products':products_new,
                                 'bins': TableCompute().process(products_new, int(ppg)),
                                 })



            scout_program_ids = request.env['scout.program'].sudo().search([])
            if scout_program_ids:
                res.qcontext.update({'scout_programs': scout_program_ids})
            else:
                res.qcontext.update({'scout_programs': False})
                
                
            if 'scout_program' in post:
                program_id = post.get('scout_program')
                products_filter = res.qcontext.get('products').filtered(lambda r:r.scout_program_id.id == int(program_id))
                res.qcontext.update({'current_program':program_id,'products':products_filter,'bins': TableCompute().process(products_filter, int(ppg))})
                
            else:
                res.qcontext.update({'current_program':False})
        
        return res
    
    
        # //rajesh 4 nov    
    
    #Check shop url======================================
    @http.route(['/get/shop/url'], type='json', auth="public", website=True,methods=['GET', 'POST'])
    def check_shop_url(self, **post):
        request.session['my_current_category'] = False
        return request.redirect('/shop')
    
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
    
    
