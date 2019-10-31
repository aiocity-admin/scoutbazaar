# coding: utf-8

import json
import logging
import base64
import dateutil.parser
import pytz
from werkzeug import urls
from odoo import http
from odoo.http import request
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_paymaya.controllers.main import PaymayaController
from odoo.tools.float_utils import float_compare
import requests

class PaymentTransaction(models.Model):
    
    _inherit="payment.transaction"
    
    def render_sale_button(self, order, submit_txt=None, render_values=None):
        values = {
            "partner_id": order.partner_shipping_id.id or order.partner_invoice_id.id,
            "billing_partner_id": order.partner_invoice_id.id,
            "order":order,
        }
        if render_values:
            values.update(render_values)
        # Not very elegant to do that here but no choice regarding the design.
        self._log_payment_transaction_sent()
        return self.acquirer_id.with_context(submit_class="btn btn-primary", submit_txt=submit_txt or _("Pay Now")).sudo().render(
            self.reference,
            order.amount_total,
            order.pricelist_id.currency_id.id,
            values=values,
        )
        
    @api.model
    def _paymaya_form_get_tx_from_data(self, data):
        
        reference = data.get('reference')
    
        transaction = self.search([('reference', '=', reference)])
        
        if not transaction:
            error_msg = (_('PayMaya: received data for reference %s; no order found') % (reference))
            raise ValidationError(error_msg)
        
        elif len(transaction) > 1:
            error_msg = (_('PayMaya: received data for reference %s; multiple orders found') % (reference))
            raise ValidationError(error_msg)
        
        return transaction
    
    
    @api.multi
    def _paymaya_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if self.acquirer_reference and data.get('reference') != self.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', data.get('reference'), self.acquirer_reference))

        return invalid_parameters
        
        
    def _paymaya_form_validate(self,data):
        
        status = data.get('paymentStatus')
        result = {}
        if status == 'PAYMENT_SUCCESS':
            result = {
            'acquirer_reference': data.get('transactionReferenceNumber'),
            'date': fields.Datetime.now(),
            }
            self._set_transaction_done()
            return self.write(result)
        else:
            error = 'Received unrecognized status for Paymaya payment %s: %s, set as error' % (self.reference, status)
            result.update(state_message=error)
            self._set_transaction_cancel()
            return self.write(result)


class AcquirerPaymaya(models.Model):
    
    
    _inherit = "payment.acquirer"
    
    
    provider = fields.Selection(selection_add=[("paymaya", "Paymaya")])
    
    merchant_name = fields.Char(string="Merchant Name")
    secret_api_key = fields.Char(string="Secret API Key")
    public_facing_api_key = fields.Char(string="Public-Facing API Key")
    
    
    @api.model
    def _get_paymaya_urls(self, environment):
        """ Paypal URLS """
        if environment == "prod":
            return {
                "paypal_form_url": "https://www.paypal.com/cgi-bin/webscr",
                "paypal_rest_url": "https://api.paypal.com/v1/oauth2/token",
            }
        else:
            return {
                "paymaya_form_url": "/redirect_payment_paymaya_page/",
            }
    
    
    @api.multi
    def paymaya_get_form_action_url(self):
        return self._get_paymaya_urls(self.environment)["paymaya_form_url"]
    
    @api.multi
    def paymaya_form_generate_values(self, values):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        paymaya_tx_values = dict(values)
        
        total_amount = {
                        "currency" : 'PHP',
                        "value" : str(round(values.get("amount"),2)),
                        "details":{
                                   "discount":"0.0",
                                   "serviceCharge": "0.0",
                                   "shippingFee": "00.00",
                                   "tax": "0.00",
                                   "subtotal": str(values.get("amount"))
                                   }
                        }
        
        buyer = {
                "firstName": values.get("partner_first_name"),
                "middleName": "",
                "lastName": values.get("partner_last_name"),
                "contact": {
                  "phone": str(values.get("partner_phone")),
                  "email": values.get("partner_email"),
                  },
                "shippingAddress": {
                      "line1": "",
                      "line2": "",
                      "city": "",
                      "state": "",
                      "zipCode":"",
                      "countryCode": ""
                    },
                "billingAddress": {
                      "line1": values.get("partner_address"),
                      "line2": "",
                      "city": values.get("partner_city"),
                      "state": values.get("partner_state").name,
                      "zipCode": values.get("partner_zip"),
                      "countryCode": "PH"
                    },
              }
        
        items = []
        
        sale_order = values.get("order")
        
        if sale_order:
            for order_line in sale_order.order_line:
                item_val = dict()
                item_val.update({
                            "name":order_line.product_id.name,
                            "code":order_line.product_id.default_code or order_line.product_id.name,
                            "description":str(order_line.name),
                            "quantity":str(round(order_line.product_uom_qty,2)),
                            "amount":{
                                        "value":str(round(order_line.price_unit,2)),
                                        "details": {
                                                    "discount":"00.00",
                                                    "subtotal":str(round(order_line.price_unit,2))
                                                    }
                                     },
                            "totalAmount": {
                                        "value": str(order_line.price_total),
                                        "details": {
                                              "discount": "00.00",
                                              "subtotal": str(round(order_line.price_total,2))
                                          }
                                    }
                            })
                items.append(item_val)
        
        
        paymaya_tx_values.update({
            "totalAmount":json.dumps(total_amount),
            "buyer":json.dumps(buyer),
            "items":json.dumps(items),
            "redirectUrl": json.dumps({
                "success": urls.url_join(base_url, PaymayaController._success_url),
                "failure": urls.url_join(base_url, PaymayaController._failure_url),
                "cancel": urls.url_join(base_url, PaymayaController._cancel_url),
                }),
           "requestReferenceNumber": values["reference"],
           "metadata": json.dumps({}),
           "secret_api_key":self.secret_api_key,
           "public_api_key":self.public_facing_api_key,
           "environment":self.environment,
         })
        return paymaya_tx_values
    
