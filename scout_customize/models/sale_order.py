# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_is_zero, pycompat

class PickingButtonValidateInherit(models.Model):
    
    _inherit='stock.picking'
    
    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit mode and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        self.env['return.order'].rmo_action_return();
        return

class SaleOrderLine(models.Model):
    
    _inherit='sale.order.line'
    
    is_gift_cart = fields.Boolean('Is Gift Card')
    gift_cart_email = fields.Char('Gift Card Email')
    is_set_multi_gift = fields.Boolean('Set Multi Gift')
    
class SaleOrderForm(models.Model):
    
    _inherit='sale.order'
    
    is_delivery_filter = fields.Boolean('Is Delivery Filter')
    all_delivery_filter = fields.Boolean('All Delivery Filter',compute="_all_delivery_order_filter")
    
    def _all_delivery_order_filter(self):
        for order in self:
            done_len = 0
            all_len = 0
            if order.picking_ids:
                for picking in order.picking_ids:
                    all_len += 1
                    if picking.state == 'done':
                        done_len += 1
                if all_len == done_len:
                    order.all_delivery_filter = True
                    order.write({'is_delivery_filter' :True})
                else:
                    order.all_delivery_filter = False
                    order.write({'is_delivery_filter' :False})
            else:
                order.all_delivery_filter = False
                order.write({'is_delivery_filter' :False})
                
                
    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        is_gift = self.env.context.get('is_gift')
        if line_id is not False and is_gift:
            line_id = False
        res = super(SaleOrderForm, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        if 'line_id' in res and 'order_line_email' in self.env.context:
            sale_order_line = self.env['sale.order.line'].sudo().search([('id','=',res.get('line_id'))])
            if sale_order_line:
                sale_order_line.update({'is_gift_cart':True,'gift_cart_email':self.env.context.get('order_line_email')})
        return res
    
#     @api.multi
#     def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
#         cart_update = super(SaleOrderForm ,self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
#         if 'line_id' in cart_update and 'order_line_email' in self.env.context:
#             sale_order_line = self.env['sale.order.line'].sudo().search([('id','=',cart_update.get('line_id'))])
#             if sale_order_line:
#                 sale_order_line.update({'is_gift_cart':True,'gift_cart_email':self.env.context.get('order_line_email')})
#         return cart_update
    
    @api.multi
    def action_confirm(self):
        res = super(SaleOrderForm ,self).action_confirm()
        for line in self.order_line:
            if line.is_gift_cart and line.is_set_multi_gift == False:
                
                coupon_program_id = self.env['sale.coupon.program'].create({
                        'active':True,
                        'name': line.order_id.name,
#                         'rule_products_domain':line.product_id.is_rule_products_domain,
#                         'rule_min_quantity':line.product_id.is_rule_min_quantity,
#                         'rule_minimum_amount':line.product_id.is_rule_minimum_amount,
#                         'rule_minimum_amount_tax_inclusion':line.product_id.is_rule_minimum_amount_tax_inclusion,
                        'validity_duration':line.product_id.product_tmpl_id.is_validity_duration,
                        'company_id': line.order_id.company_id.id,
                        'discount_line_product_id': line.product_id.id,
#                         'reward_type': line.product_id.is_gift_type,
                        'reward_type': 'discount',
                        'discount_type':line.product_id.product_tmpl_id.is_discount_type,
#                         'discount_type':'fixed_amount',
#                         'discount_percentage':line.product_id.is_discount_percentage,
                        'discount_fixed_amount':(line.product_id.product_tmpl_id.is_discount_fixed_amount) * (line.product_uom_qty),
#                         'discount_fixed_amount':line.price_unit,
#                         'discount_apply_on':line.product_id.is_discount_apply_on,
#                         'discount_specific_product_id':line.product_id.is_discount_specific_product_id.id,
#                         'discount_max_amount':line.product_id.is_discount_max_amount,
#                         'reward_product_id':line.product_id.is_reward_product_id.id,
#                         'reward_product_quantity':line.product_id.is_reward_product_quantity,
#                         'reward_product_uom_id':line.product_id.is_reward_product_uom_id,
                        'program_type':'coupon_program',
                    })
                line.update({'is_set_multi_gift':True})
                vals = {'program_id': coupon_program_id.id}
#                 for partner in self.env['res.users'].search([('partner_id.email','=',line.gift_cart_email)],limit=1):
                partner = self.env['res.users'].search([('partner_id.email','=',line.gift_cart_email)],limit=1)
                if partner:
                    vals.update({'partner_id': partner.partner_id.id,
    #                                  'program_id':coupon_program_id.id,
                                 })
                    coupon = self.env['sale.coupon'].create(vals)
                    subject = '%s, a coupon has been generated for you' % (partner.name)
                    template = self.env.ref('sale_coupon.mail_template_sale_coupon', raise_if_not_found=False)
                    if template:
                        template.send_mail(coupon.id, email_values={'email_from': line.order_id.partner_id.email or '', 'subject': subject,})
                else:
                    raise UserError(_('"'+ line.product_id.name +'" product line in Entered "Email" Username does not exists. Please check and re-enter the email.'))
        return res