from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError

class VendorUsers(models.Model):
    
    _inherit='product.template'
    
    vendor_user_product = fields.Many2one('res.users',string='Vendor User', default=lambda self: self.env.user)
    international_ids = fields.Many2many('res.partner',string="International Domestick", domain=lambda self: [("id", "in", self.vendor_user_product.partner_id.child_ids.ids)])
    # is_vendor_product = fields.Boolean('Is Vendor Product')

    @api.model_create_multi
    def create(self,vals_list):
        res = super(VendorUsers, self).create(vals_list)
        user_id = self.env['res.users'].has_group('scout_vendor.group_vendor_product')
        if user_id:
            rule_location = self.env['stock.location.route'].sudo()
            for i in res.route_ids:
                stage_ids = rule_location.search([('name','=','Dropship')])
                if stage_ids:
                    res.write({'route_ids':[(6,0,stage_ids.ids)]})
        return res
   

    # @api.multi
    # def write(self,vals):
    #     res = super(VendorUsers,self).write(vals)
    #     user_id = self.env['res.users'].has_group('scout_vendor.group_vendor_product')
    #     if user_id:
    #         rule_location = self.env['stock.location.route'].sudo()
    #         for i in res.route_ids:
    #             stage_ids = rule_location.search([('name','=','Dropship')])
    #             if stage_ids:
    #                 res.write({'route_ids':[(6,0,stage_ids.ids)]})
    #     return res


class VendorSaleOrder(models.Model):
     
    _inherit='sale.order'

    # User in Vendor mail Send ==================
    @api.multi
    def action_confirm(self):
        res = super(VendorSaleOrder, self).action_confirm()
        vendor_list = []
        for line in self.order_line:
            rule_location = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
            if line.route_id == rule_location:
                if not line.product_id.vendor_user_product.id  in vendor_list:
                    vendor_list.append(line.product_id.vendor_user_product.id)
        for vendor_user in vendor_list:
            if vendor_user:
                vendor = self.env['res.users'].sudo().search([('id','=',int(vendor_user))])
                template_id = self.env.ref('scout_vendor.mail_template_sale_order_line_dropship',False)
                if template_id:
                    template_id.sudo().write({
                        'email_to': str(vendor.email),
                        'email_from': self.env.user.company_id.email  
                    })
                    mail_id = template_id.with_context({'vendor_name':vendor.name}).send_mail(self.id, force_send=True, raise_exception=False)
        return res

#     @api.onchange('pre_country_id')
#     def onchange_code(self):
#         public_categ = self.env['product.public.category'].sudo()
#         if self.order_line:
#             storefront_categ_id = public_categ.get_storefront_category(self.order_line[0].product_id.public_categ_ids)
#             if storefront_categ_id:
#                 warehouse_id = storefront_categ_id.parent_id.child_warehouse_id
#                 self.warehouse_id = warehouse_id
#                 self.webshop_id = warehouse_id.webshop_id
#             else:
#                 if self.order_line[0].product_id.is_vendor_product:
#                     self.warehouse_id = self.order_line[0].product_id.public_categ_ids.parent_id.warehouse_id
#                 else:
#                     self.warehouse_id = False
#                     self.webshop_id = False
#         else:
#             raise UserError(_('Please Add Orderlines.'))

# class VendorCategory(models.Model):
    
#     _inherit='product.public.category'
    
#     is_vendor_category = fields.Boolean('Is Vendor Category')

#     def get_storefront_category(self,categ_id):
#         if not categ_id.is_vendor_category:
#             if categ_id.storefront_location_id:
#                 return categ_id
            
#             elif not categ_id.storefront_location_id and categ_id.parent_id:
#                 return categ_id.get_storefront_category(categ_id.parent_id)
            
#             elif not categ_id.storefront_location_id and not categ_id.parent_id:
#                 return False
    
class VendorUsersLogin(models.Model):

    _inherit='res.users'

    @api.multi
    def _is_vender_users(self):
        self.ensure_one()
        return self.has_group('scout_vendor.group_vendor_product')
