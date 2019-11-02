# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError

class ProductTemplate(models.Model):
    
    _inherit='product.template'
    
    @api.one
    def _set_weight(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.weight = self.weight
        if self.weight <= 0.0:
                raise UserError(_('product weight greater than 0.0.'))
    
    is_gift_product = fields.Boolean('Is Gift Product')
    is_gift_type = fields.Selection([
        ('discount', 'Discount'),
        ('product', 'Free Product'),
        ], string='Gift Type', default='discount',)
    is_discount_type = fields.Selection([
#         ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')], default="fixed_amount",
        help="Percentage - Entered percentage discount will be provided\n" +
        "Amount - Entered fixed amount discount will be provided")
    is_discount_percentage = fields.Float(string="Discount", default=10,
        help='The discount in percentage, between 1 to 100')
    is_discount_fixed_amount = fields.Float(string="Fixed Amount", help='The discount in fixed amount')
    is_reward_product_id = fields.Many2one('product.product', string="Free Product",
        help="Reward Product")
    is_discount_apply_on = fields.Selection([
        ('on_order', 'On Order'),
        ('cheapest_product', 'On Cheapest Product'),
        ('specific_product', 'On Specific Product')], default="on_order",
        help="On Order - Discount on whole order\n" +
        "Cheapest product - Discount on cheapest product of the order\n" +
        "Specific product - Discount on selected specific product")
    
    
    is_discount_specific_product_id = fields.Many2one('product.product', string="Product",
        help="Product that will be discounted if the discount is applied on a specific product")
    
    is_discount_max_amount = fields.Float(default=0,
        help="Maximum amount of discount that can be provided")
    is_reward_product_quantity = fields.Integer(string="Quantity", default=1, help="Reward product quantity")
    is_reward_product_uom_id = fields.Many2one(related='is_reward_product_id.product_tmpl_id.uom_id', string='Unit of Measure', readonly=True)
    is_validity_duration = fields.Integer(default=1,
        help="Validity duration for a coupon after its generation")
    is_rule_minimum_amount = fields.Float(default=0.0, help="Minimum required amount to get the reward")
    is_rule_minimum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')], default="tax_excluded")
    is_rule_products_domain = fields.Char(string="Based on Products", default=[['sale_ok', '=', True]], help="On Purchase of selected product, reward will be given")
    is_rule_min_quantity = fields.Integer(string="Minimum Quantity", default=1,
        help="Minimum required product quantity to get the reward")