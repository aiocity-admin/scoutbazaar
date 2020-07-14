# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AmountTransferredHistory(models.Model):
    
    _name = 'amount.transferred.history'
    
    
    
    
    order_id = fields.Many2one('sale.order',string="Order Reference")
    
    name = fields.Char('Name',related="order_id.name")
    
    account_received_id = fields.Many2one('account.account',string="Transferred Account")
    
    partner_id = fields.Many2one('res.partner',string="Vendor / NSO ")
    
    payment_reference = fields.Selection([
                                          ('nso',"NSO"),
                                          ('vendor',"Vendor"),
                                          ('acquirer','Acquirer'),
                                          ('shipping','Shipping'),
                                          ('market_place_nso','Market Place (NSO)'),
                                          ('market_place_vendor','Market Place (Vendor)'),
                                          ])
    
    state = fields.Selection([('draft','Draft'),('done','Done')],default='draft')
    
    currency_id = fields.Many2one('res.currency',string='Currency',related='order_id.currency_id',store=True)
    
    amount = fields.Monetary('Amount',store=True)
    
    order_date = fields.Datetime(string="Order Date",related="order_id.date_order",store=True)
    
    foreign_currency_id = fields.Many2one('res.currency',string='Foreign Currency',compute='compute_foreign_currency')
    
    foreign_currency_amount = fields.Monetary(string='Foreign Currency',compute='compute_foreign_currency',currency_field = 'foreign_currency_id')
    
    
    
    @api.multi
    @api.depends('currency_id','amount','account_received_id','order_id')
    def compute_foreign_currency(self):
        
        for transfer in self:
            if transfer.order_id.is_transfer_paid_order and transfer.account_received_id.currency_id and transfer.account_received_id.currency_id.name == 'PHP' and transfer.currency_id.name != 'PHP':
                transfer.foreign_currency_id = transfer.account_received_id.currency_id
                transfer.foreign_currency_amount = transfer.currency_id._convert(transfer.amount, transfer.account_received_id.currency_id, self.env.user.company_id, transfer.order_id.date_order)
            else:
                transfer.foreign_currency_id = transfer.currency_id
                transfer.foreign_currency_amount = 0.0
                
    @api.multi
    def set_to_draft(self):
        for history_id in self:
            history_id.write({'state':'draft'})
            
            
    @api.multi
    def set_to_done(self):
        for history_id in self:
            history_id.write({'state':'done'})
            
    