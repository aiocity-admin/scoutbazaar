# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AmountTransferredConfirm(models.TransientModel):
    
    
    _name = 'amount.transfer.confirm'
    
    
    
    
    @api.multi
    def amount_transfer_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['amount.transferred.history'].browse(active_ids):
            if record.state != 'draft':
                raise UserError(_("Selected amount transfer(s) cannot be set to 'Done' as they are not in 'Draft' state."))
            else:
                record.set_to_done()
        return {'type': 'ir.actions.act_window_close'}
    