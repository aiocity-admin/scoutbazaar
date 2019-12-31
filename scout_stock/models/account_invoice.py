from odoo import api, models, fields, _
from odoo.exceptions import UserError

class AccountInvoiceFormLine(models.Model):
    
    _inherit = "account.invoice.line"
    
    location_id = fields.Many2one("stock.location", related="sale_line_ids.location_id" , string="Location")
    delivery_method = fields.Many2one("delivery.carrier", related="sale_line_ids.delivery_method" ,string="Delivery Method")
    shipping_charge = fields.Float("Shipping Charge", compute='_compute_account_invoice_shipping_charge')
    extra_charge_product = fields.Float("Extra Charge", compute='_compute_account_invoice_extra_charge_product')
    delivery_charge = fields.Float(string="Delivery Charge", compute='_compute_account_invoice_delivery_charge')
    
    @api.one
    @api.depends('sale_line_ids')
    def _compute_account_invoice_shipping_charge(self):
        if self.sale_line_ids:
            for line in self.sale_line_ids:
                if line.shipping_charge:
                    self.shipping_charge = line.shipping_charge
     
    @api.one
    @api.depends('sale_line_ids')
    def _compute_account_invoice_extra_charge_product(self):
        if self.sale_line_ids:
            for line in self.sale_line_ids:
                if line.extra_charge_product:
                    self.extra_charge_product = line.extra_charge_product
     
    @api.one
    @api.depends('sale_line_ids')
    def _compute_account_invoice_delivery_charge(self):
        if self.sale_line_ids:
            for line in self.sale_line_ids:
                if line.delivery_charge:
                    self.delivery_charge = line.delivery_charge
    
    
# class SaleOrderTOInvoiceLine(models.Model):
#     
#     _inherit = "sale.order.line"
#     
#     @api.multi
#     def _prepare_invoice_line(self, qty):
#         res = super(SaleOrderTOInvoiceLine, self)._prepare_invoice_line(qty)
#         if self:
#             res.update({'shipping_charge': self.shipping_charge,
#                         'extra_charge_product': self.extra_charge_product,
#                         'delivery_charge':self.delivery_charge,
#                         })
#         return res
