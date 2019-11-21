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
         
#          Website Sale Order Create========================

        for order in sale_transaction:
            line_location = order.order_line.filtered(lambda r:r.location_id)
            line_vendor = order.order_line.filtered(lambda r:r.product_id.is_vendor_product)
            nso_group = {}
            product_extra_charge_ph = 0.0
            company_account_tranfer = 0.0
            vendor_delivery_group = {}
            vendor_cost_price = {}
            vendor_extra_charge = 0.0
            vendor_company_tranfer = 0.0
            for l_loc in line_location:
                product_ph_sum = 0.0
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
                    
            for vendor_line in line_vendor:
                vendor_ph_sum = 0.0
                vendor_product_cost_price = 0.0
                if not vendor_line.delivery_method in vendor_delivery_group:
                    vendor_shipping_charge = vendor_line.shipping_charge
                    vendor_extra = vendor_line.extra_charge_product
                    vendor_handline = (vendor_shipping_charge * handling_charge)/100
                    vendor_charge = vendor_shipping_charge - vendor_handline
                    company_charge = order.company_id.vendor_transfer_margin_id
                    product_price = vendor_line.price_unit
                    company_total = (product_price * company_charge)/100
                    vendor_ph_sum += vendor_charge
                    vendor_company_tranfer += company_total
                    vendor_extra_charge += vendor_extra
                    vendor_delivery_group.update({vendor_line.delivery_method:vendor_ph_sum})
                else:
                    vendor_shipping_charge = vendor_line.shipping_charge
                    vendor_extra = vendor_line.extra_charge_product
                    vendor_handline = (vendor_shipping_charge * handling_charge)/100
                    vendor_charge = vendor_shipping_charge - vendor_handline
                    company_charge = order.company_id.vendor_transfer_margin_id
                    product_price = vendor_line.price_unit
                    company_total = (product_price * company_charge)/100
                    vendor_ph_sum += vendor_charge
                    vendor_company_tranfer += company_total
                    vendor_extra_charge += vendor_extra
                    vendor_delivery_group[vendor_line.delivery_method] += vendor_ph_sum
                    
                if not vendor_line.product_id.vendor_user_product in vendor_cost_price:
                    product_cost_price = vendor_line.product_id.standard_price
                    vendor_product_cost_price += product_cost_price
                    vendor_cost_price.update({vendor_line.product_id.vendor_user_product:vendor_product_cost_price})
                else:
                    product_cost_price = vendor_line.product_id.standard_price
                    vendor_product_cost_price += product_cost_price
                    vendor_cost_price[vendor_line.product_id.vendor_user_product] += vendor_product_cost_price
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
                credit_move_line_src_payment_company = {
                                'name':order.name + '/' + 'Credit' or '/',
                                'debit':False,
                                'credit':company_account_tranfer,
                                'account_id':order.company_id.vendor_account_id.property_account_receivable_id.id,
                                'currency_id':order.currency_id.id,
                                'date':fields.Date().today(),
                                'date_maturity':fields.Date().today(),
                                }
                debit_move_line_src_payment_company = {
                               'name':order.name + '/' + 'Debit' or '/',
                               'debit':company_account_tranfer,
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
                                               'partner_id':order.company_id.vendor_account_id,
                                               'payment_reference':'market_place',
                                               'amount':price_invoice_company_extra,
                                               })
                move_vals_payment_company = {
                     'ref':order.name,
                     'line_ids':lines_payment_company,
                     'journal_id': main_journal_id.journal_id.id,
                     'date':fields.Date().today(),
                     }
                ctx['company_id'] = order.company_id.id
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
                
            if vendor_delivery_group:
                vendor_lines = []
                for delivery in vendor_delivery_group:
                    amount = vendor_delivery_group[delivery]
                    credit_move_line_src = {
                                        'name':order.name + '/' + 'Credit' or '/',
                                        'debit':False,
                                        'credit':amount,
                                        'account_id':delivery.delivery_account_id.id,
                                        'currency_id':order.currency_id.id,
                                        'date':fields.Date().today(),
                                        'date_maturity':fields.Date().today(),
                                        }
                    vendor_lines.append((0,0,credit_move_line_src))
                    debit_move_line_src = {
                                   'name':order.name + '/' + 'Debit' or '/',
                                   'debit':amount,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                    vendor_lines.append((0,0,debit_move_line_src))
                    
                    #History Code===========================
                    amount_transferred_history_obj.create({
                                                   'account_received_id':delivery.delivery_account_id.id,
                                                   'order_id':order.id,
                                                   'partner_id':False,
                                                   'payment_reference':'shipping',
                                                   'amount':amount,
                                                   })
                ctx ={}
                vendor_move_vals = {
                     'ref':order.name,
                     'line_ids':vendor_lines,
                     'journal_id': main_journal_id.journal_id.id,
                     'date': fields.Date().today(),
                     }
                ctx['company_id'] = order.company_id.id
                move = AccountMove.with_context(ctx).create(vendor_move_vals)
                move.post()
                
            if vendor_cost_price:
                lines_payment_cost = []
                for vendor in vendor_cost_price:
                    amount = vendor_cost_price[vendor]
                    credit_vendor_move_line_src_payment_company = {
                                    'name':order.name + '/' + 'Credit' or '/',
                                    'debit':False,
                                    'credit':amount,
                                    'account_id':vendor.partner_id.property_account_receivable_id.id,
                                    'currency_id':order.currency_id.id,
                                    'date':fields.Date().today(),
                                    'date_maturity':fields.Date().today(),
                                    }
                    lines_payment_cost.append((0,0,credit_vendor_move_line_src_payment_company))
                    debit_vendor_move_line_src_payment_company = {
                                   'name':order.name + '/' + 'Debit' or '/',
                                   'debit':amount,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                    lines_payment_cost.append((0,0,debit_vendor_move_line_src_payment_company))
                    
                    #History Code===========================
                    amount_transferred_history_obj.create({
                                                   'account_received_id':vendor.partner_id.property_account_receivable_id.id,
                                                   'order_id':order.id,
                                                   'partner_id':vendor.partner_id.id,
                                                   'payment_reference':'vendor',
                                                   'amount':amount,
                                                   })
                ctx ={}
                move_vals_payment_vendor = {
                     'ref':order.name,
                     'line_ids':lines_payment_cost,
                     'journal_id': main_journal_id.journal_id.id,
                     'date':fields.Date().today(),
                     }
                ctx['company_id'] = order.company_id.id
                move_payment_vendor = AccountMove.with_context(ctx).create(move_vals_payment_vendor)
                move_payment_vendor.post()
                
            if vendor_company_tranfer:
                lines_payment_company = []
                credit_vendor_move_line_src_payment_company = {
                                'name':order.name + '/' + 'Credit' or '/',
                                'debit':False,
                                'credit':vendor_company_tranfer,
                                'account_id':order.company_id.vendor_account_id.property_account_receivable_id.id,
                                'currency_id':order.currency_id.id,
                                'date':fields.Date().today(),
                                'date_maturity':fields.Date().today(),
                                }
                debit_vendor_move_line_src_payment_company = {
                               'name':order.name + '/' + 'Debit' or '/',
                               'debit':vendor_company_tranfer,
                               'credit':False,
                               'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                               'currency_id':order.currency_id.id,
                               'date': fields.Date().today(),
                               'date_maturity': fields.Date().today(),
                               }
                ctx ={}
                
                #History Code===========================
                amount_transferred_history_obj.create({
                                                   'account_received_id':order.company_id.vendor_account_id.property_account_receivable_id.id,
                                                   'order_id':order.id,
                                                   'partner_id':order.company_id.vendor_account_id.id,
                                                   'payment_reference':'market_place',
                                                   'amount':vendor_company_tranfer,
                                                   })
                lines_payment_company.append((0,0,credit_vendor_move_line_src_payment_company))
                lines_payment_company.append((0,0,debit_vendor_move_line_src_payment_company))
                move_vals_payment_vendor_company = {
                     'ref':order.name,
                     'line_ids':lines_payment_company,
                     'journal_id': main_journal_id.journal_id.id,
                     'date':fields.Date().today(),
                     }
                ctx['company_id'] = order.company_id.id
                move_payment_vendor_company = AccountMove.with_context(ctx).create(move_vals_payment_vendor_company)
                move_payment_vendor_company.post()
                
            if vendor_extra_charge:
                lines_payment_extra = []
                credit_vendor_move_line_src_payment_extra = {
                                'name':order.name + '/' + 'Credit' or '/',
                                'debit':False,
                                'credit':vendor_extra_charge,
                                'account_id':order.transaction_ids.acquirer_id.payment_acquirer_id.id,
                                'currency_id':order.currency_id.id,
                                'date':fields.Date().today(),
                                'date_maturity':fields.Date().today(),
                                }
                debit_vendor_move_line_src_payment_extra = {
                               'name':order.name + '/' + 'Debit' or '/',
                               'debit':vendor_extra_charge,
                               'credit':False,
                               'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                               'currency_id':order.currency_id.id,
                               'date': fields.Date().today(),
                               'date_maturity': fields.Date().today(),
                               }
                ctx ={}
                
                #History Code===========================
                amount_transferred_history_obj.create({
                                                   'account_received_id':order.transaction_ids.acquirer_id.payment_acquirer_id.id,
                                                   'order_id':order.id,
                                                   'partner_id':False,
                                                   'payment_reference':'acquirer',
                                                   'amount':vendor_extra_charge,
                                                   })
                lines_payment_extra.append((0,0,credit_vendor_move_line_src_payment_extra))
                lines_payment_extra.append((0,0,debit_vendor_move_line_src_payment_extra))
                move_vals_payment_vendor_extra = {
                     'ref':order.name,
                     'line_ids':lines_payment_extra,
                     'journal_id': main_journal_id.journal_id.id,
                     'date':fields.Date().today(),
                     }
                ctx['company_id'] = order.company_id.id
                move_payment_vendor_extra = AccountMove.with_context(ctx).create(move_vals_payment_vendor_extra)
                move_payment_vendor_extra.post()
            order.update({'is_settled':True})
            
#         Backend Sale Order Create===========================

        for invoice_order in sale_invoice:
            invoice_order_total = invoice_order.amount_total
            for invoice in invoice_order.invoice_ids:
                invoice_total = invoice.amount_total
                percentage = (invoice_total * 100)/invoice_order_total
                line_location = invoice_order.order_line.filtered(lambda r:r.location_id)
                line_vendor = invoice_order.order_line.filtered(lambda r:r.product_id.is_vendor_product)
                nso_group = {}
                company_account_tranfer = 0.0
                product_extra_charge_ph = 0.0
                vendor_delivery_group = {}
                vendor_cost_price = {}
                vendor_extra_charge = 0.0
                vendor_company_tranfer = 0.0
                for l_loc in line_location:
                    product_ph_sum = 0.0
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
                for vendor_line in line_vendor:
                    vendor_ph_sum = 0.0
                    vendor_product_cost_price = 0.0
                    if not vendor_line.delivery_method in vendor_delivery_group:
                        vendor_shipping_charge = vendor_line.shipping_charge
                        vendor_extra = vendor_line.extra_charge_product
                        vendor_handline = (vendor_shipping_charge * handling_charge)/100
                        vendor_charge = vendor_shipping_charge - vendor_handline
                        company_charge = invoice_order.company_id.vendor_transfer_margin_id
                        product_price = vendor_line.price_unit
                        company_total = (product_price * company_charge)/100
                        vendor_ph_sum += vendor_charge
                        vendor_company_tranfer += company_total
                        vendor_extra_charge += vendor_extra
                        vendor_delivery_group.update({vendor_line.delivery_method:vendor_ph_sum})
                    else:
                        vendor_shipping_charge = vendor_line.shipping_charge
                        vendor_extra = vendor_line.extra_charge_product
                        vendor_handline = (vendor_shipping_charge * handling_charge)/100
                        vendor_charge = vendor_shipping_charge - vendor_handline
                        company_charge = invoice_order.company_id.vendor_transfer_margin_id
                        product_price = vendor_line.price_unit
                        company_total = (product_price * company_charge)/100
                        vendor_ph_sum += vendor_charge
                        vendor_company_tranfer += company_total
                        vendor_extra_charge += vendor_extra
                        vendor_delivery_group[vendor_line.delivery_method] += vendor_ph_sum
                        
                    if not vendor_line.product_id.vendor_user_product in vendor_cost_price:
                        product_cost_price = vendor_line.product_id.standard_price
                        vendor_product_cost_price += product_cost_price
                        vendor_cost_price.update({vendor_line.product_id.vendor_user_product:vendor_product_cost_price})
                    else:
                        product_cost_price = vendor_line.product_id.standard_price
                        vendor_product_cost_price += product_cost_price
                        vendor_cost_price[vendor_line.product_id.vendor_user_product] += vendor_product_cost_price
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
                    
                if vendor_delivery_group:
                    vendor_lines = []
                    for delivery in vendor_delivery_group:
                        amount = vendor_delivery_group[delivery]
                        vendor_invoice = (amount * percentage)/100
                        credit_move_line_src = {
                                            'name':invoice_order.name + '/' + 'Credit' or '/',
                                            'debit':False,
                                            'credit':vendor_invoice,
                                            'account_id':delivery.delivery_account_id.id,
                                            'currency_id':invoice_order.currency_id.id,
                                            'date':fields.Date().today(),
                                            'date_maturity':fields.Date().today(),
                                            }
                        vendor_lines.append((0,0,credit_move_line_src))
                        debit_move_line_src = {
                                       'name':invoice_order.name + '/' + 'Debit' or '/',
                                       'debit':vendor_invoice,
                                       'credit':False,
                                       'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                       'currency_id':invoice_order.currency_id.id,
                                       'date': fields.Date().today(),
                                       'date_maturity': fields.Date().today(),
                                       }
                        vendor_lines.append((0,0,debit_move_line_src))
                        #History Code===========================
                        amount_transferred_history_obj.create({
                                                   'account_received_id':delivery.delivery_account_id.id,
                                                   'order_id':invoice_order.id,
                                                   'partner_id':False,
                                                   'payment_reference':'shipping',
                                                   'amount':vendor_invoice,
                                                   })
                    ctx ={}
                    vendor_move_vals = {
                                         'ref':invoice_order.name,
                                         'line_ids':vendor_lines,
                                         'journal_id': main_journal_id.journal_id.id,
                                         'date': fields.Date().today(),
                                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move = AccountMove.with_context(ctx).create(vendor_move_vals)
                    move.post()
                    
                if vendor_cost_price:
                    lines_payment_cost = []
                    for vendor in vendor_cost_price:
                        amount = vendor_cost_price[vendor]
                        vendor_invoice_cost_price = (amount * percentage)/100
                        credit_vendor_move_line_src_payment_company = {
                                        'name':invoice_order.name + '/' + 'Credit' or '/',
                                        'debit':False,
                                        'credit':vendor_invoice_cost_price,
                                        'account_id':vendor.partner_id.property_account_receivable_id.id,
                                        'currency_id':invoice_order.currency_id.id,
                                        'date':fields.Date().today(),
                                        'date_maturity':fields.Date().today(),
                                        }
                        lines_payment_cost.append((0,0,credit_vendor_move_line_src_payment_company))
                        debit_vendor_move_line_src_payment_company = {
                                       'name':invoice_order.name + '/' + 'Debit' or '/',
                                       'debit':vendor_invoice_cost_price,
                                       'credit':False,
                                       'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                       'currency_id':invoice_order.currency_id.id,
                                       'date': fields.Date().today(),
                                       'date_maturity': fields.Date().today(),
                                       }
                        lines_payment_cost.append((0,0,debit_vendor_move_line_src_payment_company))
                        
                        #History Code===========================
                        amount_transferred_history_obj.create({
                                                   'account_received_id':vendor.partner_id.property_account_receivable_id.id,
                                                   'order_id':invoice_order.id,
                                                   'partner_id':vendor.partner_id.id,
                                                   'payment_reference':'vendor',
                                                   'amount':vendor_invoice_cost_price,
                                                   })
                    ctx ={}
                    move_vals_payment_vendor = {
                                         'ref':invoice_order.name,
                                         'line_ids':lines_payment_cost,
                                         'journal_id': main_journal_id.journal_id.id,
                                         'date':fields.Date().today(),
                                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move_payment_vendor = AccountMove.with_context(ctx).create(move_vals_payment_vendor)
                    move_payment_vendor.post()
                    
                if vendor_company_tranfer:
                    lines_payment_company = []
                    vendor_invoice_company = (vendor_company_tranfer * percentage)/100
                    credit_vendor_move_line_src_payment_company = {
                                    'name':invoice_order.name + '/' + 'Credit' or '/',
                                    'debit':False,
                                    'credit':vendor_invoice_company,
                                    'account_id':invoice_order.company_id.vendor_account_id.property_account_receivable_id.id,
                                    'currency_id':invoice_order.currency_id.id,
                                    'date':fields.Date().today(),
                                    'date_maturity':fields.Date().today(),
                                    }
                    debit_vendor_move_line_src_payment_company = {
                                   'name':invoice_order.name + '/' + 'Debit' or '/',
                                   'debit':vendor_invoice_company,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':invoice_order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                    ctx ={}
                    lines_payment_company.append((0,0,credit_vendor_move_line_src_payment_company))
                    lines_payment_company.append((0,0,debit_vendor_move_line_src_payment_company))
                    
                    #History Code===========================
                    amount_transferred_history_obj.create({
                                                   'account_received_id':invoice_order.company_id.vendor_account_id.property_account_receivable_id.id,
                                                   'order_id':invoice_order.id,
                                                   'partner_id':invoice_order.company_id.vendor_account_id.id,
                                                   'payment_reference':'market_place',
                                                   'amount':vendor_invoice_company,
                                                   })
                    move_vals_payment_vendor_company = {
                         'ref':invoice_order.name,
                         'line_ids':lines_payment_company,
                         'journal_id': main_journal_id.journal_id.id,
                         'date':fields.Date().today(),
                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move_payment_vendor_company = AccountMove.with_context(ctx).create(move_vals_payment_vendor_company)
                    move_payment_vendor_company.post()
                    
                if vendor_extra_charge:
                    lines_payment_extra = []
                    vendor_invoice_extra = (vendor_extra_charge * percentage)/100
                    credit_vendor_move_line_src_payment_extra = {
                                    'name':invoice_order.name + '/' + 'Credit' or '/',
                                    'debit':False,
                                    'credit':vendor_invoice_extra,
                                    'account_id':invoice.payment_journal_id.default_credit_account_id.id,
                                    'currency_id':invoice_order.currency_id.id,
                                    'date':fields.Date().today(),
                                    'date_maturity':fields.Date().today(),
                                    }
                    debit_vendor_move_line_src_payment_extra = {
                                   'name':invoice_order.name + '/' + 'Debit' or '/',
                                   'debit':vendor_invoice_extra,
                                   'credit':False,
                                   'account_id':main_journal_id.journal_id.default_debit_account_id.id,
                                   'currency_id':invoice_order.currency_id.id,
                                   'date': fields.Date().today(),
                                   'date_maturity': fields.Date().today(),
                                   }
                    ctx ={}
                    lines_payment_extra.append((0,0,credit_vendor_move_line_src_payment_extra))
                    lines_payment_extra.append((0,0,debit_vendor_move_line_src_payment_extra))
                    
                    #History Code===========================
                    amount_transferred_history_obj.create({
                                                   'account_received_id':invoice.payment_journal_id.default_credit_account_id.id,
                                                   'order_id':invoice_order.id,
                                                   'partner_id':False,
                                                   'payment_reference':'acquirer',
                                                   'amount':vendor_invoice_extra,
                                                   })
                    move_vals_payment_vendor_extra = {
                         'ref':invoice_order.name,
                         'line_ids':lines_payment_extra,
                         'journal_id': main_journal_id.journal_id.id,
                         'date':fields.Date().today(),
                         }
                    ctx['company_id'] = invoice_order.company_id.id
                    move_payment_vendor_extra = AccountMove.with_context(ctx).create(move_vals_payment_vendor_extra)
                    move_payment_vendor_extra.post()
            invoice_order.update({'is_settled':True})
