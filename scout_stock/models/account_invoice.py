# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'
        
    transfer_journal_id = fields.Many2one('account.journal','Transfer Journal')
    
    
    @api.multi
    def action_validate_invoice_payment(self):
        active_id = self._context.get('active_id')
        account_invoice = self.env['account.invoice'].browse(active_id)
        account_invoice.write({'payment_journal_id':self.transfer_journal_id.id})
        return super(AccountPayment,self).action_validate_invoice_payment()
    
    
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    payment_journal_id = fields.Many2one('account.journal','Payment Journal')