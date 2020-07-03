from odoo import api, models, fields, _

class SaleOrderShipping(models.Model):
    _inherit = 'sale.order'
    
    @api.onchange('partner_shipping_id')
    def partner_shipping_onchange(self):
        for order in self.order_line:
            if order.location_id:
                if order.location_id.nso_location_id.country_id == self.partner_shipping_id.country_id:
                    return {'domain': {'delivery_method': [('source_country_ids','=',self.partner_shipping_id.country_id.id)]}}
    
    @api.multi
    def calculate_nso_lines_order(self,order):
        sale_order_line_obj = self.env['sale.order.line'].sudo()
        delivery_product = self.env.ref('delivery.product_product_delivery').sudo()
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        payment_processing_fee = res_config.payment_processing_fee
        if order.currency_id != order.company_id.currency_id:
            payment_processing_fee = order.currency_id._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
        is_cod_order = False
        for line in order.order_line:
            if line.location_id:
                nso_location_lines = order.order_line.filtered(lambda r:r.location_id.nso_location_id == line.location_id.nso_location_id)
                if nso_location_lines:
                    delivery_charge = 0.0
                    for n_line in nso_location_lines:
                        delivery_charge += n_line.delivery_charge
                        nso_line = order.order_line.filtered(lambda r: r.name == "Total Shipping and Handling Fees(" + line.location_id.nso_location_id.name + '-' + line.location_id.nso_location_id.country_id.name + ")")
                    if not order.is_cod_order:
                        for n_line in nso_location_lines:
                            delivery_charge += n_line.extra_charge_product
                            is_cod_order = True
                        delivery_charge += payment_processing_fee
                if nso_line:
                    nso_line.write({'price_unit':delivery_charge})
                else:
                    vals = {
							'order_id':order.id,
							'name':"Total Shipping and Handling Fees(" + line.location_id.nso_location_id.name + '-' + line.location_id.nso_location_id.country_id.name + ")",
							'product_id':delivery_product.id,
							'product_uom':delivery_product.sudo().uom_id.id,
							'price_unit':delivery_charge,
							'product_uom_qty':1.0,
							'is_nso_delivery_line':True
							}
                    if delivery_charge > 0:
                        sale_order_line_obj.create(vals)
    
    def vendor_lines_calculate(self,order):
        sale_order_line_obj = self.env['sale.order.line'].sudo()
        delivery_product = self.env.ref('delivery.product_product_delivery').sudo()
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        payment_processing_fee = res_config.payment_processing_fee
        delivery_charge = 0.0
        is_cod_order = False
        for line in order.order_line:
            statge_id = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
            if not line.location_id and line.product_id.route_ids in statge_id:
                delivery_charge += line.delivery_charge
                if not order.is_cod_order:
                    delivery_charge += line.extra_charge_product
                    is_cod_order = True
                    delivery_charge += payment_processing_fee
        # if is_cod_order:

        delivery_line = order.order_line.filtered(lambda r:r.name == "Total Shipping and Handling Charges(Dropshipper)")
        if delivery_line:
            delivery_line.write({'price_unit':delivery_charge})
        else:
            vals = {
				'order_id':order.id,
				'name':'Total Shipping and Handling Charges(Dropshipper)',
				'product_id': delivery_product.id,
				'product_uom':delivery_product.sudo().uom_id.id,
				'price_unit':delivery_charge,
				'product_uom_qty':1.0,
				'is_vendor_delivery_line':True
				}
            if delivery_charge > 0:
                sale_order_line_obj.create(vals)
    
    @api.multi
    def button_calculate_nso_lines_order(self): 
        nso_delivery_lines = self.order_line.filtered(lambda r:r.is_nso_delivery_line)
        nso_delivery_lines.update({'delivery_charge':0.0})
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        for order in self:
            nso_diff_country_code_group_list = {}
            nso_same_country_code_group = order.order_line.filtered(lambda n: n.delivery_method and n.location_id.nso_location_id.country_id.code == order.partner_shipping_id.country_id.code)
            nso_diff_country_code_group = order.order_line.filtered(lambda n: n.delivery_method and n.location_id.nso_location_id.country_id.code != order.partner_shipping_id.country_id.code)
            
            #Same Source Destination Code====================
            nso_same_country_location_group = {}
            same_delivery_price = 0.0
            for c_group in nso_same_country_code_group:
                if c_group.location_id in nso_same_country_location_group:
                    nso_same_country_location_group[c_group.location_id] |= c_group
                else:
                    nso_same_country_location_group.update({c_group.location_id:c_group})
            for nso_loc in nso_same_country_location_group:
                same_carrier = nso_same_country_location_group[nso_loc][0].delivery_method
                if same_carrier:
                    res_price = getattr(same_carrier, '%s_rate_line_shipment' % same_carrier.delivery_type)(order,nso_same_country_location_group[nso_loc])
                    if not res_price.get('error_message'):
                        currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                        if currency:
                            if order.currency_id != order.company_id.currency_id:
                                payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                        handling_price = (res_price.get('price') *handling_charge)/100
                        price_total = 0.0
                        for s_line in nso_same_country_location_group[nso_loc]:
                            price_total += s_line.price_total
                        if order.is_cod_order:
                            temp_price = 0.0
                            same_delivery_price += round((handling_price + res_price.get('price')),2)
                            delivery_price_split = (handling_price + res_price.get('price'))/len(nso_same_country_location_group[nso_loc])
                            shipping_price_split = res_price.get('price')/len(nso_same_country_location_group[nso_loc])
                            extra_charge_split = temp_price/len(nso_same_country_location_group[nso_loc])
                        else:
                            temp_price = ((payment_processing_fee + res_price.get('price') + price_total + handling_price) / (1 - transaction_value/100) - (payment_processing_fee + res_price.get('price') + price_total + handling_price))
                            same_delivery_price += round((handling_price + payment_processing_fee + temp_price + res_price.get('price')),2)
                            delivery_price_split = (handling_price + res_price.get('price'))/len(nso_same_country_location_group[nso_loc])
                            shipping_price_split = res_price.get('price')/len(nso_same_country_location_group[nso_loc])
                            extra_charge_split = temp_price/len(nso_same_country_location_group[nso_loc])
                        nso_same_country_location_group[nso_loc].write({
                                                                   'delivery_method':same_carrier.id,
                                                                   'delivery_charge':delivery_price_split,
                                                                   'shipping_charge':shipping_price_split,
                                                                   'extra_charge_product':extra_charge_split,
                                                                })
                        order.calculate_nso_lines_order(order)
            #Different Source Destination Code====================
            for diff_country in nso_diff_country_code_group:
                if not diff_country.location_id.nso_location_id.country_id in nso_diff_country_code_group_list:
                    nso_diff_country_code_group_list.update({diff_country.location_id.nso_location_id.country_id:diff_country})
                else:
                    nso_diff_country_code_group_list[diff_country.location_id.nso_location_id.country_id] |= diff_country
            for nso_group_list in nso_diff_country_code_group_list:
                nso_country_code_group = nso_diff_country_code_group_list[nso_group_list]
                nso_country_location_group = {}
                carrier = nso_country_code_group[0].delivery_method
                delivery_price = 0.0
                for c_group in nso_country_code_group:
                    if c_group.location_id in nso_country_location_group:
                        nso_country_location_group[c_group.location_id] |= c_group
                    else:
                        nso_country_location_group.update({c_group.location_id:c_group})
                for nso_loc in nso_country_location_group:
                    if carrier:
                        res_price = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,nso_country_location_group[nso_loc])
                        if not res_price.get('error_message'):
                            currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                            if currency:
                                if order.currency_id != order.company_id.currency_id:
                                    payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                            handling_price = (res_price.get('price') *handling_charge)/100
                            price_total = 0.0
                            for s_line in nso_country_location_group[nso_loc]:
                                price_total += s_line.price_total
                            if order.is_cod_order:
                                temp_price = 0.0
                                delivery_price_split = (handling_price + res_price.get('price'))/len(nso_country_location_group[nso_loc])
                                delivery_price += round((handling_price + res_price.get('price')),2)
                                shipping_price_split = res_price.get('price')/len(nso_country_location_group[nso_loc])
                                extra_charge_split = temp_price/len(nso_country_location_group[nso_loc])
                            else:
                                temp_price = ((payment_processing_fee + res_price.get('price') + price_total + handling_price) / (1 - transaction_value/100) - (payment_processing_fee + res_price.get('price') + price_total + handling_price))
                                delivery_price_split = (handling_price + res_price.get('price'))/len(nso_country_location_group[nso_loc])
                                delivery_price += round((handling_price + payment_processing_fee + temp_price + res_price.get('price')),2)
                                shipping_price_split = res_price.get('price')/len(nso_country_location_group[nso_loc])
                                extra_charge_split = temp_price/len(nso_country_location_group[nso_loc])
                            nso_country_location_group[nso_loc].write({
                                                                   'delivery_charge':delivery_price_split,
                                                                   'shipping_charge':shipping_price_split,
                                                                   'extra_charge_product':extra_charge_split,
                                                                })
                            order.calculate_nso_lines_order(order)
            order.vendor_product_calculate(order)
    
    def vendor_product_calculate(self,order):
        vendor_delivery_lines = order.order_line.filtered(lambda r:r.is_vendor_delivery_line)
        vendor_delivery_lines.update({'delivery_charge':0.0})
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
        vendor_country_code_group = order.order_line.filtered(lambda n: n.delivery_method and not n.location_id and n.product_id.route_ids in stage_ids)
        vendor_same_country_based_group = {}
        vendor_diff_country_based_group = {}
        for v_group in vendor_country_code_group:
            vendor = self.get_stock_vendor(order,v_group)
            if vendor.country_id == order.partner_shipping_id.country_id:
                if vendor in vendor_same_country_based_group:
                    vendor_same_country_based_group[vendor] |= v_group
                else:
                    vendor_same_country_based_group.update({vendor:v_group})
            else:
                if vendor in vendor_diff_country_based_group:
                    vendor_diff_country_based_group[vendor] |= v_group
                else:
                    vendor_diff_country_based_group.update({vendor:v_group})
        
        #Same Source destination code==================================
        same_delivery_price = 0.0
        for v_cnt in vendor_same_country_based_group:
            same_carrier = vendor_same_country_based_group[v_cnt][0].delivery_method
            if same_carrier:
                if v_cnt.country_id.code == order.partner_shipping_id.country_id.code:
                    res_price = getattr(same_carrier, '%s_rate_line_shipment' % same_carrier.delivery_type)(order,vendor_same_country_based_group[v_cnt])
                    if not res_price.get('error_message'):
                        currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                        if currency:
                            if order.currency_id != order.company_id.currency_id:
                                payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                        handling_price = (res_price.get('price') *handling_charge)/100
                        price_total = 0.0
                        for s_line in vendor_same_country_based_group[v_cnt]:
                            price_total += s_line.price_total
                        if order.is_cod_order:
                            temp_price = 0.0
                            delivery_price_split = (handling_price + res_price.get('price'))/len(vendor_same_country_based_group[v_cnt])
                            shipping_price_split = res_price.get('price')/len(vendor_same_country_based_group[v_cnt])
                            extra_charge_split = temp_price/len(vendor_same_country_based_group[v_cnt])
                        else:
                            temp_price = ((payment_processing_fee + res_price.get('price') + price_total + handling_price) / (1 - transaction_value/100) - (payment_processing_fee + res_price.get('price') + price_total + handling_price))
                            delivery_price_split = (handling_price + res_price.get('price'))/len(vendor_same_country_based_group[v_cnt])
                            shipping_price_split = res_price.get('price')/len(vendor_same_country_based_group[v_cnt])
                            extra_charge_split = temp_price/len(vendor_same_country_based_group[v_cnt])
                        vendor_same_country_based_group[v_cnt].write({
                                                               'delivery_charge':delivery_price_split,
                                                               'shipping_charge':shipping_price_split,
                                                               'extra_charge_product':extra_charge_split,
                                                            })
                        order.vendor_lines_calculate(order)
        
        #Different Source Destination Code====================
        for v_diff_cnt in vendor_diff_country_based_group:
            carrier = vendor_diff_country_based_group[v_diff_cnt][0].delivery_method
            delivery_price = 0.0
            if carrier:
                res_price = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,vendor_diff_country_based_group[v_diff_cnt])
                if not res_price.get('error_message'):
                    currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                    if currency:
                        if order.currency_id != order.company_id.currency_id:
                            payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                    handling_price = (res_price.get('price') *handling_charge)/100
                    price_total = 0.0
                    for s_line in vendor_diff_country_based_group[v_diff_cnt]:
                        price_total += s_line.price_total
                    if order.is_cod_order:
                        temp_price = 0.0
                        delivery_price += round((handling_price + res_price.get('price')),2)
                        delivery_price_split = (handling_price + res_price.get('price'))/len(vendor_diff_country_based_group[v_diff_cnt])
                        shipping_price_split = res_price.get('price')/len(vendor_diff_country_based_group[v_diff_cnt])
                        extra_charge_split = temp_price/len(vendor_diff_country_based_group[v_diff_cnt])
                    else:
                        temp_price = ((payment_processing_fee + res_price.get('price') + price_total + handling_price) / (1 - transaction_value/100) - (payment_processing_fee + res_price.get('price') + price_total + handling_price))
                        delivery_price += round((handling_price + payment_processing_fee + temp_price + res_price.get('price')),2)
                        delivery_price_split = (handling_price + res_price.get('price'))/len(vendor_diff_country_based_group[v_diff_cnt])
                        shipping_price_split = res_price.get('price')/len(vendor_diff_country_based_group[v_diff_cnt])
                        extra_charge_split = temp_price/len(vendor_diff_country_based_group[v_diff_cnt])
                    vendor_diff_country_based_group[v_diff_cnt].write({
                                                           'delivery_charge':delivery_price_split,
                                                           'shipping_charge':shipping_price_split,
                                                           'extra_charge_product':extra_charge_split,
                                                        })
                    order.vendor_lines_calculate(order)
                    
