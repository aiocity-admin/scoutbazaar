# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_settled = fields.Boolean("Is settled?", readonly=True)
    
    @api.model
    def _run_payment_transfer_shipping(self):
        sale_transaction_id = self.env['sale.order'].sudo().search([
                                                                    ('state','=','sale'),
                                                                    ('transaction_ids','!=',False),
                                                                    ('is_settled','=',False),
                                                                    ])
        amount_transferred_history_obj = self.env['amount.transferred.history'].sudo()
        sale_transaction_state_id = self.env['sale.order'].sudo()
        for tran_order in sale_transaction_id:
            transaction_state = True
            for tr_id in tran_order.transaction_ids:
                if not tr_id.state == 'done':
                    transaction_state = False
                if transaction_state:
                    sale_transaction_state_id |= tran_order
                    
        sale_invoice_id = self.env['sale.order'].sudo().search([
                                                              ('transaction_ids','=',False),
                                                              ('is_settled','=',False),
                                                              ('state','=','sale'),
                                                              ])
        sale_invoice_state_id = self.env['sale.order'].sudo()
         
        for inv_order in sale_invoice_id:
            invoice_state = True
            amount = 0.0
            for in_id in inv_order.invoice_ids:
                if not in_id.state == 'paid':
                    invoice_state = False
                else:
                    amount_total_inv = in_id.amount_total_signed
                    amount += amount_total_inv
                    invoice_state = True
            if invoice_state:
                if inv_order.amount_total <= amount:
                    sale_invoice_state_id |= inv_order
                     
        sale_transaction = []
        sale_invoice = []
        for i in sale_transaction_state_id:
            sale_transaction.append(i)
        for j in sale_invoice_state_id:
            sale_invoice.append(j)
        AccountMove = self.env['account.move'].sudo()
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
         
        for order in sale_transaction:
            line_location = order.order_line.filtered(lambda r:r.location_id)
            nso_group = {}
            product_extra_charge_ph = 0.0
            company_account_tranfer = 0.0
            for l_loc in line_location:
                product_ph_sum = 0.0
                account_id_nso = l_loc.location_id.nso_location_id.property_account_receivable_id.id
                if not l_loc.location_id.nso_location_id in nso_group:
                    product_shipping_charge = l_loc.shipping_charge
                    product_extra_charge= l_loc.extra_charge_product
                    product_handlind = (product_shipping_charge * handling_charge)/100
                    product_charge = product_shipping_charge - product_handlind
                    company_charge = order.company_id.vendor_account_id.transfer_margin
                    product_price = l_loc.price_subtotal
                    company_charge_sum = (product_price * company_charge)/100
                    product_sum = product_charge + company_charge_sum
                    product_ph_sum += product_sum
                    product_extra_charge_ph += product_extra_charge
                    company_margin = order.company_id.vendor_transfer_margin_id
                    company_total = (product_price * company_margin)/100
                    company_account_tranfer += company_total
                    nso_group.update({l_loc.location_id.nso_location_id:product_ph_sum})
                else:
                    product_shipping_charge = l_loc.shipping_charge
                    product_extra_charge= l_loc.extra_charge_product
                    product_handlind = (product_shipping_charge * handling_charge)/100
                    product_charge = product_shipping_charge - product_handlind
                    company_charge = order.company_id.vendor_account_id.transfer_margin
                    product_price = l_loc.price_subtotal
                    company_charge_sum = (product_price * company_charge)/100
                    product_sum = product_charge + company_charge_sum
                    product_ph_sum += product_sum
                    product_extra_charge_ph += product_extra_charge
                    company_margin = order.company_id.vendor_transfer_margin_id
                    company_total = (product_price * company_margin)/100
                    company_account_tranfer += company_total
                    nso_group[l_loc.location_id.nso_location_id] += product_ph_sum
            main_journal_id = order.invoice_ids.payment_move_line_ids.mapped('move_id')
            if nso_group:
                lines = []
                for nso_partner in nso_group:
                    nso_amount = 0.0
                    nso_margin = nso_partner.transfer_margin
                    nso_group_order_line = order.order_line.filtered(lambda n:n.location_id and n.location_id.nso_location_id == nso_partner)
                    for nso_amt_line in nso_group_order_line:
                        nso_amount += nso_amt_line.price_total
                    nso_transfer = (nso_amount * nso_margin)/100
                    amount = nso_group[nso_partner]
                    amount += nso_transfer
                    if nso_partner.parent_id and nso_partner.is_nso:
                        credit_move_line_src = {
                                            'name':order.name + '/' + 'Credit' or '/',
                                            'debit':False,
                                            'credit':amount,
                                            'account_id':nso_partner.child_account_id.id,
                                            'currency_id':order.currency_id.id,
                                            'date':fields.Date().today(),
                                            'date_maturity':fields.Date().today(),
                                            }
                        lines.append((0,0,credit_move_line_src))
                        
                        #History Code===========================
                        amount_transferred_history_obj.create({
                                                       'account_received_id':nso_partner.child_account_id.id,
                                                       'order_id':order.id,
                                                       'partner_id':nso_partner.id,
                                                       'payment_reference':'nso',
                                                       'amount':amount
                                                       })
                    else:
                        credit_move_line_src = {
                                            'name':order.name + '/' + 'Credit' or '/',
                                            'debit':False,
                                            'credit':amount,
                                            'account_id':nso_partner.property_account_receivable_id.id,
                                            'currency_id':order.currency_id.id,
                                            'date':fields.Date().today(),
                                            'date_maturity':fields.Date().today(),
                                            }
                        lines.append((0,0,credit_move_line_src))
                        
                        #History Code===========================
                        amount_transferred_history_obj.create({
                                                       'account_received_id':nso_partner.property_account_receivable_id.id,
                                                       'order_id':order.id,
                                                       'partner_id':nso_partner.id,
                                                       'payment_reference':'nso',
                                                       'amount':amount
                                                       })
                    debit_move_line_src = {
                                       'name':order.name + '/' + 'Debit' or '/',
                                       'debit':amount,
                                       'credit':False,
                                       'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                       'currency_id':order.currency_id.id,
                                       'date': fields.Date().today(),
                                       'date_maturity': fields.Date().today(),
                                       }
                    lines.append((0,0,debit_move_line_src))
                ctx ={}
                move_vals = {
                         'ref':order.name,
                         'line_ids':lines,
                         'journal_id': main_journal_id.journal_id.id,
                         'date': fields.Date().today(),
                         }
                ctx['company_id'] = order.company_id.id
                move = AccountMove.with_context(ctx).create(move_vals)
                move.post()
                
            if company_account_tranfer:
                lines_payment_company = []
                price_invoice_company_extra = (company_account_tranfer * percentage)/100
                credit_move_line_src_payment_company = {
                                'name':order.name + '/' + 'Credit' or '/',
                                'debit':False,
                                'credit':price_invoice_company_extra,
                                'account_id':order.company_id.vendor_account_id.property_account_receivable_id.id,
                                'currency_id':order.currency_id.id,
                                'date':fields.Date().today(),
                                'date_maturity':fields.Date().today(),
                                }
                debit_move_line_src_payment_company = {
                               'name':order.name + '/' + 'Debit' or '/',
                               'debit':price_invoice_company_extra,
                               'credit':False,
                               'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                               'currency_id':order.currency_id.id,
                               'date': fields.Date().today(),
                               'date_maturity': fields.Date().today(),
                               }
                ctx ={}
                lines_payment_company.append((0,0,credit_move_line_src_payment_company))
                lines_payment_company.append((0,0,debit_move_line_src_payment_company))
                
                #History Code===========================
                amount_transferred_history_obj.create({
                                               'account_received_id':order.company_id.vendor_account_id.property_account_receivable_id.id,
                                               'order_id':order.id,
                                               'partner_id':False,
                                               'payment_reference':'market_place',
                                               'amount':price_invoice_company_extra,
                                               })
                move_vals_payment_company = {
                     'ref':invoice_order.name,
                     'line_ids':lines_payment_company,
                     'journal_id': main_journal_id.journal_id.id,
                     'date':fields.Date().today(),
                     }
                ctx['company_id'] = invoice_order.company_id.id
                move_payment_company = AccountMove.with_context(ctx).create(move_vals_payment_company)
                move_payment_company.post()
                
            if product_extra_charge_ph:
                lines_payment_acquirer = []
                credit_move_line_src_payment_acquirer = {
                                    'name':order.name + '/' + 'Credit' or '/',
                                    'debit':False,
                                    'credit':product_extra_charge_ph,
                                    'account_id':order.transaction_ids.acquirer_id.payment_acquirer_id.id,
                                    'currency_id':order.currency_id.id,
                                    'date':fields.Date().today(),
                                    'date_maturity':fields.Date().today(),
                                    }
                debit_move_line_src_payment_acquirer = {
                                   'name':order.name + '/' + 'Debit' or '/',
                                   'debit':product_extra_charge_ph,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                ctx ={}
                lines_payment_acquirer.append((0,0,credit_move_line_src_payment_acquirer))
                lines_payment_acquirer.append((0,0,debit_move_line_src_payment_acquirer))
                move_vals_payment_acquirer = {
                         'ref':order.name,
                         'line_ids':lines_payment_acquirer,
                         'journal_id': main_journal_id.journal_id.id,
                         'date':fields.Date().today(),
                         }
                ctx['company_id'] = order.company_id.id
                move_payment_acquirer = AccountMove.with_context(ctx).create(move_vals_payment_acquirer)
                
                
                #History Code===========================
                amount_transferred_history_obj.create({
                                               'account_received_id':order.transaction_ids.acquirer_id.payment_acquirer_id.id,
                                               'order_id':order.id,
                                               'partner_id':False,
                                               'payment_reference':'acquirer',
                                               'amount':product_extra_charge_ph,
                                               })
                move_payment_acquirer.post()
                    
            order.update({'is_settled':True})
            
        for invoice_order in sale_invoice:
            invoice_order_total = invoice_order.amount_total
            for invoice in invoice_order.invoice_ids:
                invoice_total = invoice.amount_total
                percentage = (invoice_total * 100)/invoice_order_total
                line_location = invoice_order.order_line.filtered(lambda r:r.location_id)
                nso_group = {}
                company_account_tranfer = 0.0
                product_extra_charge_ph = 0.0
                for l_loc in line_location:
                    product_ph_sum = 0.0
                    account_id_nso = l_loc.location_id.nso_location_id.property_account_receivable_id.id
                    if not l_loc.location_id.nso_location_id in nso_group:
                        product_shipping_charge = l_loc.shipping_charge
                        product_extra_charge= l_loc.extra_charge_product
                        product_handlind = (product_shipping_charge * handling_charge)/100
                        product_charge = product_shipping_charge - product_handlind
                        company_charge = invoice_order.company_id.vendor_account_id.transfer_margin
                        product_price = l_loc.price_unit
                        company_charge_sum = (product_price * company_charge)/100
                        product_sum = product_charge + company_charge_sum
                        product_ph_sum += product_sum
                        product_extra_charge_ph += product_extra_charge
                        company_margin = invoice_order.company_id.vendor_transfer_margin_id
                        company_total = (product_price * company_margin)/100
                        company_account_tranfer += company_total
                        nso_group.update({l_loc.location_id.nso_location_id:product_ph_sum})
                    else:
                        product_shipping_charge = l_loc.shipping_charge
                        product_extra_charge= l_loc.extra_charge_product
                        product_handlind = (product_shipping_charge * handling_charge)/100
                        product_charge = product_shipping_charge - product_handlind
                        company_charge = invoice_order.company_id.vendor_account_id.transfer_margin
                        product_price = l_loc.price_subtotal
                        company_charge_sum = (product_price * company_charge)/100
                        product_sum = product_charge + company_charge_sum
                        product_ph_sum += product_sum
                        product_extra_charge_ph += product_extra_charge
                        company_margin = invoice_order.company_id.vendor_transfer_margin_id
                        company_total = (product_price * company_margin)/100
                        company_account_tranfer += company_total
                        nso_group[l_loc.location_id.nso_location_id] += product_ph_sum
                main_journal_id = invoice.payment_move_line_ids.mapped('move_id')
                if nso_group:
                    lines = []
                    for nso_partner in nso_group:
                        amount = nso_group[nso_partner]
                        nso_amount = 0.0
                        nso_margin = nso_partner.transfer_margin
                        nso_group_order_line = invoice_order.order_line.filtered(lambda n:n.location_id and n.location_id.nso_location_id == nso_partner)
                        for nso_amt_line in nso_group_order_line:
                            nso_amount += nso_amt_line.price_total
                        nso_transfer = (nso_amount * nso_margin)/100
                        amount += nso_transfer
                        price_invoice_nso = (amount * percentage)/100
                        if nso_partner.parent_id and nso_partner.is_nso:
                            credit_move_line_src = {
                                            'name':invoice_order.name + '/' + 'Credit' or '/',
                                            'debit':False,
                                            'credit':price_invoice_nso,
                                            'account_id':nso_partner.child_account_id.id,
                                            'currency_id':invoice_order.currency_id.id,
                                            'date':fields.Date().today(),
                                            'date_maturity':fields.Date().today(),
                                            }
                            lines.append((0,0,credit_move_line_src))
                            
                            #History Code===========================
                            amount_transferred_history_obj.create({
                                                           'account_received_id':nso_partner.child_account_id.id,
                                                           'order_id':invoice_order.id,
                                                           'partner_id':nso_partner.id,
                                                           'payment_reference':'nso',
                                                           'amount':price_invoice_nso,
                                                           })
                        else:
                            credit_move_line_src = {
                                            'name':invoice_order.name + '/' + 'Credit' or '/',
                                            'debit':False,
                                            'credit':price_invoice_nso,
                                            'account_id':nso_partner.property_account_receivable_id.id,
                                            'currency_id':invoice_order.currency_id.id,
                                            'date':fields.Date().today(),
                                            'date_maturity':fields.Date().today(),
                                            }
                            lines.append((0,0,credit_move_line_src))
                            
                            #History Code===========================
                            amount_transferred_history_obj.create({
                                                           'account_received_id':nso_partner.property_account_receivable_id.id,
                                                           'order_id':invoice_order.id,
                                                           'partner_id':nso_partner.id,
                                                           'payment_reference':'nso',
                                                           'amount':price_invoice_nso,
                                                           })
                        debit_move_line_src = {
                                       'name':invoice_order.name + '/' + 'Debit' or '/',
                                       'debit':price_invoice_nso,
                                       'credit':False,
                                       'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                       'currency_id':invoice_order.currency_id.id,
                                       'date': fields.Date().today(),
                                       'date_maturity': fields.Date().today(),
                                       }
                        lines.append((0,0,debit_move_line_src))
                    ctx ={}
                    move_vals = {
                         'ref':invoice_order.name,
                         'line_ids':lines,
                         'journal_id': main_journal_id.journal_id.id,
                         'date': fields.Date().today(),
                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move = AccountMove.with_context(ctx).create(move_vals)
                    move.post()
                    
                if company_account_tranfer:
                    lines_payment_company = []
                    price_invoice_company_extra = (company_account_tranfer * percentage)/100
                    print("\n\n--------------price_invoice_company_extra---------------",price_invoice_company_extra)
                    credit_move_line_src_payment_company = {
                                    'name':invoice_order.name + '/' + 'Credit' or '/',
                                    'debit':False,
                                    'credit':price_invoice_company_extra,
                                    'account_id':invoice_order.company_id.vendor_account_id.property_account_receivable_id.id,
                                    'currency_id':invoice_order.currency_id.id,
                                    'date':fields.Date().today(),
                                    'date_maturity':fields.Date().today(),
                                    }
                    debit_move_line_src_payment_company = {
                                   'name':invoice_order.name + '/' + 'Debit' or '/',
                                   'debit':price_invoice_company_extra,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':invoice_order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                    ctx ={}
                    
                    #History Code===========================
                    amount_transferred_history_obj.create({
                                                   'account_received_id':invoice_order.company_id.vendor_account_id.property_account_receivable_id.id,
                                                   'order_id':invoice_order.id,
                                                   'partner_id':invoice_order.company_id.vendor_account_id.id,
                                                   'payment_reference':'market_place',
                                                   'amount':price_invoice_company_extra,
                                                   })
                    lines_payment_company.append((0,0,credit_move_line_src_payment_company))
                    lines_payment_company.append((0,0,debit_move_line_src_payment_company))
                    move_vals_payment_acquirer = {
                         'ref':invoice_order.name,
                         'line_ids':lines_payment_company,
                         'journal_id': main_journal_id.journal_id.id,
                         'date':fields.Date().today(),
                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move_payment_acquirer = AccountMove.with_context(ctx).create(move_vals_payment_acquirer)
                    move_payment_acquirer.post()
                    
                if product_extra_charge_ph:
                    lines_payment_acquirer = []
                    price_invoice_extra = (product_extra_charge_ph * percentage)/100
                    credit_move_line_src_payment_acquirer = {
                                    'name':invoice_order.name + '/' + 'Credit' or '/',
                                    'debit':False,
                                    'credit':price_invoice_extra,
                                    'account_id':invoice.payment_journal_id.default_credit_account_id.id,
                                    'currency_id':invoice_order.currency_id.id,
                                    'date':fields.Date().today(),
                                    'date_maturity':fields.Date().today(),
                                    }
                    debit_move_line_src_payment_acquirer = {
                                   'name':invoice_order.name + '/' + 'Debit' or '/',
                                   'debit':price_invoice_extra,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':invoice_order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                    ctx ={}
                    lines_payment_acquirer.append((0,0,credit_move_line_src_payment_acquirer))
                    lines_payment_acquirer.append((0,0,debit_move_line_src_payment_acquirer))
                    
                    #History Code===========================
                    amount_transferred_history_obj.create({
                                                   'account_received_id':invoice.payment_journal_id.default_credit_account_id.id,
                                                   'order_id':invoice_order.id,
                                                   'partner_id':False,
                                                   'payment_reference':'acquirer',
                                                   'amount':price_invoice_extra,
                                                   })
                    move_vals_payment_acquirer = {
                         'ref':invoice_order.name,
                         'line_ids':lines_payment_acquirer,
                         'journal_id': main_journal_id.journal_id.id,
                         'date':fields.Date().today(),
                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move_payment_acquirer = AccountMove.with_context(ctx).create(move_vals_payment_acquirer)
                    move_payment_acquirer.post()
                    
            invoice_order.update({'is_settled':True})
