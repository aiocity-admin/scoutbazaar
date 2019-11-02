from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError

class VendorUsers(models.Model):
    
    _inherit='product.template'
    
    vendor_user_product = fields.Many2one('res.users',string='Vendor User', default=lambda self: self.env.user)
    
    is_vendor_product = fields.Boolean('Is Vendor Product')
    

class VendorSaleOrder(models.Model):
     
    _inherit='sale.order'
     
    @api.onchange('pre_country_id')
    def onchange_code(self):
        public_categ = self.env['product.public.category'].sudo()
        if self.order_line:
            storefront_categ_id = public_categ.get_storefront_category(self.order_line[0].product_id.public_categ_ids)
            if storefront_categ_id:
                warehouse_id = storefront_categ_id.parent_id.child_warehouse_id
                self.warehouse_id = warehouse_id
                self.webshop_id = warehouse_id.webshop_id
            else:
                if self.order_line[0].product_id.is_vendor_product:
                    self.warehouse_id = self.order_line[0].product_id.public_categ_ids.parent_id.warehouse_id
                else:
                    self.warehouse_id = False
                    self.webshop_id = False
        else:
            raise UserError(_('Please Add Orderlines.'))

class VendorCategory(models.Model):
    
    _inherit='product.public.category'
    
    is_vendor_category = fields.Boolean('Is Vendor Category')

    def get_storefront_category(self,categ_id):
        if not categ_id.is_vendor_category:
            if categ_id.storefront_location_id:
                return categ_id
            
            elif not categ_id.storefront_location_id and categ_id.parent_id:
                return categ_id.get_storefront_category(categ_id.parent_id)
            
            elif not categ_id.storefront_location_id and not categ_id.parent_id:
                return False
    
class VendorUsersLogin(models.Model):

    _inherit='res.users'

    @api.multi
    def _is_vender_users(self):
        self.ensure_one()
        return self.has_group('scout_vendor.group_vendor_product')