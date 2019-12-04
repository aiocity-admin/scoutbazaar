# -*- coding: utf-8 -*-

import json
import logging
import pprint
import base64
import requests
import werkzeug
from werkzeug import urls

from odoo import http
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymayaController(http.Controller):
    
    _success_url = '/payment/paymaya/success/'
    _failure_url = '/payment/paymaya/failure/'
    _cancel_url = '/payment/paymaya/cancel/'
    checkoutID = ''
    reference = ''
    secret_key = ''
    public_key = ''
    environment = ''
    
    @http.route('/redirect_payment_paymaya_page/', type='http', auth='none', methods=['POST'], csrf=False)
    def paymaya_token_url_page(self, **post):
        data = dict()
        
        #Get Data from the form
        totalAmount = json.loads(post.get('totalAmount'))
        buyer = json.loads(post.get('buyer'))
        items = json.loads(post.get('items'))
        redirectUrl = json.loads(post.get('redirectUrl'))
        requestReferenceNumber = post.get('requestReferenceNumber')
        metadata = json.loads(post.get('metadata'))
        data.update({
                     'totalAmount':totalAmount,
                     'buyer':buyer,
                     'items':items,
                     'redirectUrl':redirectUrl,
                     'requestReferenceNumber':requestReferenceNumber,
                     'metadata':metadata
                     })
        
        #Pass Values and get token url
        public_key = post.get('public_api_key')
        secret_key = post.get('secret_api_key')
        public_key_encoded = public_key.encode("utf-8")
        self.secret_key = secret_key
        self.public_key = public_key
        self.environment = post.get('environment')
        
        
        if post.get('environment') == 'prod':
            url = "https://pg.paymaya.com/checkout/v1/checkouts/"
        else:
            url = "https://pg-sandbox.paymaya.com/checkout/v1/checkouts/"
           
        headers = {"Authorization": "Basic %s" % base64.b64encode(public_key_encoded).decode('utf-8'),"Content-Type": "application/json"}
        
        r = requests.post(url=url,json=data,headers=headers)
        imported = json.loads(r.text)
        if imported:
            if 'redirectUrl' in imported:
                self.checkoutID = imported['checkoutId']
                self.reference = post.get('requestReferenceNumber')
                return werkzeug.utils.redirect(imported['redirectUrl'])
        return werkzeug.utils.redirect('https://www.google.com')
    
    
    @http.route('/payment/paymaya/success', type='http', auth='none', csrf=False)
    def paymaya_success(self, **post):
        secret_key_encode = self.secret_key.encode("utf-8")
        if self.environment == 'prod':
            url = 'https://pg.paymaya.com/checkout/v1/checkouts/' + str(self.checkoutID)
        else:
            url = 'https://pg-sandbox.paymaya.com/checkout/v1/checkouts/' + str(self.checkoutID)
        
        headers = {"Authorization": "Basic %s" % base64.b64encode(secret_key_encode).decode('utf-8')}
        response = requests.get(url=url,headers=headers)
        if response.text:
            response_data = json.loads(response.text)
            response_data.update({'reference':self.reference})
            request.env['payment.transaction'].sudo().form_feedback(response_data, 'paymaya')
        return werkzeug.utils.redirect('/payment/process')
    
            
    @http.route('/payment/paymaya/failure', type='http', auth='none', methods=['GET','POST'], csrf=False)
    def paymaya_failure(self, **post):
        post.update({"reference":self.reference})
        request.env['payment.transaction'].sudo().form_feedback(post, 'paymaya')
        return werkzeug.utils.redirect('/payment/process')
        
        
    @http.route('/payment/paymaya/cancel', type='http', auth='none', methods=['GET','POST'], csrf=False)
    def paymaya_cancel(self, **post):
        post.update({"reference":self.reference})
        request.env['payment.transaction'].sudo().form_feedback(post, 'paymaya')
        return werkzeug.utils.redirect('/payment/process')
        
