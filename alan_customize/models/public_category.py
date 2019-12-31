# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WebsiteProductCategory(models.Model):
    _inherit = 'product.public.category'
    
    description = fields.Html('Description for Category', translate=True)
    
    # Get Thirdparty_url======================================
    def get_thirdparty_url(self,categ_id):
        catge_dup = categ_id
        if categ_id.is_thirdparty_order:
            if categ_id.thirdparty_url:
                return categ_id.thirdparty_url
            else:
                return False
        elif categ_id.parent_id:
            return self.get_thirdparty_url(categ_id.parent_id)
        else:
            return False
        
        