# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AmountTransferredHistory(models.Model):
    
    _name = 'amount.transferred.history'
    
    
    order_id = fields.Many2one('sale.order',string="Order Reference")
    
    account_received_id = fields.Many2one('account.account',string="Transferred Account")
    
    partner_id = fields.Many2one('res.partner',string="Vendor / NSO ")
    
    payment_reference = fields.Selection([
                                          ('nso',"NSO"),
                                          ('vendor',"Vendor"),
                                          ('acquirer','Acquirer'),
                                          ('shipping','Shipping'),
                                          ('market_place','Market Place')
                                          ])
    
    state = fields.Selection([('draft','Draft'),('done','Done')])
    
    currency_id = fields.Many2one('res.currency',string='Currency',related='order_id.currency_id',store=True)
    
    amount = fields.Monetary('Amount',store=True)
    
    order_date = fields.Datetime(string="Order Date",related="order_id.date_order",store=True)