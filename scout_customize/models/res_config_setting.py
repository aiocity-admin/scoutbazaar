# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_count_page = fields.Integer(string='Product set')


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        product_count_page = int(ICPSudo.get_param('scout_customize.product_count_page'))
        
        res.update(
            product_count_page=product_count_page,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        
        self.env['ir.config_parameter'].set_param('scout_customize.product_count_page', str(self.product_count_page))
        
