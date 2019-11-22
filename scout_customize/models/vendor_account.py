# -*- coding: utf-8 -*-
from odoo import fields,models,api,_

class delivaryaccount(models.Model):
	_inherit="delivery.carrier"

	delivery_account_id = fields.Many2one('account.account',string="Account")

class paymentacquirer(models.Model):
	_inherit="payment.acquirer"

	payment_acquirer_id = fields.Many2one('account.account',string="Account")

class vendoraccount(models.Model):
	_inherit="res.company"

	vendor_account_id = fields.Many2one('res.partner',string="SB Partner")
	vendor_transfer_margin_id=fields.Float(string="SB Partner Margin")
	
class transfermargin(models.Model):
   
    _inherit="res.partner"
    
    transfer_margin = fields.Float(string="Transfer Margin")
