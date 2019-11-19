# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_count_page = fields.Integer(string='Product set', default=4)


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

        if self.product_count_page <= 0:
            raise ValidationError('Product Count is required and must be greater than 0.')
        else:
            self.env['ir.config_parameter'].set_param('scout_customize.product_count_page', str(self.product_count_page))
