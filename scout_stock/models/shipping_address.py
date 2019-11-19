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
		for order in self:
			if self.env.user.has_group('account.group_show_line_subtotals_tax_excluded'):
				order.nso_amount_delivery = sum(order.order_line.filtered('is_nso_delivery_line').mapped('price_subtotal'))
			else:
				order.nso_amount_delivery = sum(order.order_line.filtered('is_nso_delivery_line').mapped('price_total'))
		sale_order_line_obj = self.env['sale.order.line'].sudo()
		delivery_product = self.env.ref('delivery.product_product_delivery').sudo()

		for line in order.order_line:
			if line.location_id:
				nso_location_lines = order.order_line.filtered(lambda r:r.location_id.nso_location_id == line.location_id.nso_location_id)
				if nso_location_lines:
					delivery_charge = 0.0
					for n_line in nso_location_lines:
						delivery_charge += n_line.delivery_charge
				nso_line = order.order_line.filtered(lambda r: r.name == "Total Shipping and Handling Fees(" + line.location_id.nso_location_id.country_id.name + ")")

				if nso_line:
					nso_line.write({'price_unit':delivery_charge})
				else:
					vals = {
							'order_id':order.id,
							'name':"Total Shipping and Handling Fees(" + line.location_id.nso_location_id.country_id.name + ")",
							'product_id':delivery_product.id,
							'product_uom':delivery_product.sudo().uom_id.id,
							'price_unit':delivery_charge,
							'product_uom_qty':1.0,
							'is_nso_delivery_line':True
							}
					
					if delivery_charge > 0:
						sale_order_line_obj.create(vals)

	def stock_vendor_get(self,order,line):
		partner_shipping_id = order.partner_shipping_id
		partner_country_state = line.product_id.international_ids.filtered(lambda r:r.country_id == partner_shipping_id.country_id and r.state_id == partner_shipping_id.state_id)
		if partner_country_state:
			return partner_country_state
		else:
			partner_country = line.product_id.international_ids.filtered(lambda r:r.country_id == partner_shipping_id.country_id)
			if partner_country:
				return partner_country
			else:
				return line.product_id.international_ids[0]

	def vendor_lines_calculate(self,order):
		sale_order_line_obj = self.env['sale.order.line'].sudo()
		delivery_product = self.env.ref('delivery.product_product_delivery').sudo()
		delivery_charge = 0.0
		for line in order.order_line:
			statge_id = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
			if not line.location_id and line.product_id.route_ids in statge_id:
				delivery_charge += line.delivery_charge
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
	def button_calculate_nso_lines_order(self,order):
		nso_delivery_lines = self.order_line.filtered(lambda r:r.is_nso_delivery_line)
		nso_delivery_lines.update({'delivery_charge':0.0})
		res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
		handling_charge = res_config.handling_charge
		payment_processing_fee = res_config.payment_processing_fee
		transaction_value = res_config.transaction_value
		for order in self:
			for line in self.order_line:
				if line.location_id:
					if line.location_id.nso_location_id.country_id == order.partner_shipping_id.country_id:
						delivery_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
						if not delivery_carrier:
							delivery_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)
						if delivery_carrier:
							res_price = getattr(delivery_carrier, '%s_rate_line_shipment' % delivery_carrier.delivery_type)(order,line)
							if not res_price.get('error_message'):
								currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
								if currency:
									if order.currency_id != order.company_id.currency_id:
										payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
								handling_price = (res_price.get('price') *handling_charge)/100
								temp_price = payment_processing_fee + ((transaction_value/100) * (line.price_total + res_price.get('price') + handling_price))
								line.write({
									'delivery_method':delivery_carrier.id,
									'delivery_charge':res_price.get('price') + temp_price,
									'shipping_charge':res_price.get('price'),
									'extra_charge_product':temp_price
									})
								order.calculate_nso_lines_order(order)
					else:
						country_code = line.location_id.nso_location_id.country_id.code
						carrier = line.delivery_method if line.delivery_method else False
						country_id = line.location_id.nso_location_id.country_id
						delivery_price = 0.0
						lines_to_change = {}
						
						if carrier:
							for so_line in order.order_line:
								if so_line.location_id:
									if so_line.location_id.nso_location_id.country_id.code == country_code:
										res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,so_line)
										if res.get('error_message'):
											return res.get('error_message')
										else:
											currency = self.env['res.currency'].sudo().search([('name','=',res.get('currency_code'))])

											if currency:
												if order.currency_id != order.company_id.currency_id:
													payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
											handling_price = (res.get('price') *handling_charge)/100
											temp_price = payment_processing_fee + ((transaction_value/100) * (line.price_total + res.get('price') + handling_price))
											shipping_charge = payment_processing_fee + (transaction_value/100) * (so_line.price_unit + handling_charge + 1)
											lines_to_change.update({so_line:res.get('price') + temp_price})
											delivery_price += (res.get('price') + temp_price) 
							if lines_to_change:
								for change_line in lines_to_change:
									line_id = self.env['sale.order.line'].sudo().browse(change_line.id)
									if line_id:
										line_id.write({
														'delivery_method':carrier.id,
														'delivery_charge':lines_to_change[change_line],
														'shipping_charge':res.get('price'),
														'extra_charge_product':temp_price
														})
										order.calculate_nso_lines_order(order)
								delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
																										('country_id','=',country_id.id),
																										('order_id','=',order.id),
																										('is_vendor_track','=',False)
																										],limit=1)

								if delivery_line_track_ids:
									delivery_line_track_ids.update({
																	'carrier_id':carrier.id,
																	'delivery_price':round(delivery_price,2),
																	'is_vendor_track':False
																	})
								else:
									self.env['delivery.line.track'].sudo().create({
																					'country_id':country_id.id,
																					'order_id':order.id,
																					'carrier_id':carrier.id,
																					'delivery_price':round(delivery_price,2),
																					'is_vendor_track':False
																					})
					order.vendor_product_calculate(order)

		# Vendor Product Calculate code============================================
		
	def vendor_product_calculate(self,order):
		vendor_delivery_line = order.order_line.filtered(lambda r:r.is_vendor_delivery_line)
		print("\n\n--------------vendor_delivery_line----------",vendor_delivery_line)
		vendor_delivery_line.update({'delivery_charge':0.0})
		res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
		handling_charge = res_config.handling_charge
		payment_processing_fee = res_config.payment_processing_fee
		transaction_value = res_config.transaction_value

		statge_id = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
		vendor_country_code_group = order.order_line.filtered(lambda n: not n.location_id and n.product_id.route_ids in statge_id)
		vendor_same_country_based_group = {}
		vendor_diff_country_based_group = {}

		for v_group in vendor_country_code_group:
			vendor = self.stock_vendor_get(order,v_group)
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

		# Same source destination code========================================

		same_carrier = False
		same_delivery_price = 0.0

		if vendor_same_country_based_group:
			same_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
			if not same_carrier:
				same_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)

		for v_cnt in vendor_same_country_based_group:
			if v_cnt.country_id.code == order.partner_shipping_id.country_id.code:
				res_price = getattr(same_carrier, '%s_rate_line_shipment' % same_carrier.delivery_type)(order,vendor_same_country_based_group[v_cnt])
				if res_price.get('error_message'):
					res_price.get('error_message')
				else:
					currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
					if currency:
						if order.currency_id != order.company_id.currency_id:
							payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
					handling_price = (res_price.get('price') * handling_charge)/100
					price_total = 0.0
					for s_line in vendor_same_country_based_group[v_cnt]:
						price_total += s_line.price_total
					temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
					same_delivery_price += (temp_price + res_price.get('price'))
					delivery_price_split = (temp_price + res_price.get('price'))/len(vendor_same_country_based_group[v_cnt])
					vendor_same_country_based_group[v_cnt].write({
																'delivery_method':same_carrier.id,
																'delivery_charge':delivery_price_split
																})
					order.vendor_lines_calculate(order)

		if same_carrier:
			delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
																					('country_id','=',order.partner_shipping_id.country_id.id),
																					('order_id','=',order.id),
																					('is_vendor_track','=',True)
																					],limit=1)
			if delivery_line_track_ids:
				delivery_line_track_ids.update({
												'carrier_id':same_carrier.id,
												'delivery_price':round(same_delivery_price,2),
												'is_vendor_track':True
												})
			else:
				self.env['delivery.line.track'].sudo().create({
															'country_id':order.partner_shipping_id.country_id.id,
															'order_id':order.id,
															'carrier_id':same_carrier.id,
															'delivery_price':round(same_delivery_price,2),
															'is_vendor_track':True
															})

		# Difference Source Distination Code=======================================
		for v_diff_cnt in vendor_diff_country_based_group:
			carrier = vendor_diff_country_based_group[v_diff_cnt][0].delivery_method
			country_id = v_diff_cnt.country_id.id
			if not carrier:
				carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[country_id]),('shipping_range','=','international')],limit=1)
			delivery_price = 0.0
			if carrier:
				res_price = getattr(carrier,'%s_rate_line_shipment' % carrier.delivery_type)(order,vendor_diff_country_based_group[v_diff_cnt])
				if res_price.get('error_message'):
					res_price.get('error_message')
				else:
					currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
					if currency:
						if order.currency_id != order.company_id.currency_id:
							payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
					handling_price = (res_price.get('price') * handling_charge)/100
					price_total = 0.0
					for s_line in vendor_diff_country_based_group[v_diff_cnt]:
						price_total += so_line.price_total
					temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
					delivery_charge += (temp_price + res_price.get('price'))
					delivery_price_split = (temp_price + res_price.get('price'))/len(vendor_diff_country_based_group[v_diff_cnt])
					vendor_diff_country_based_group[v_diff_cnt].write({
																	'delivery_method':carrier.id,
																	'delivery_charge':delivery_price_split
																	}) 
					order.vendor_lines_calculate(order)
					
			delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
																					('country_id','=',country_id),
																					('order_id','=',order.id),
																					('is_vendor_track','=',True)
																					],limit=1)
			if delivery_line_track_ids:
				delivery_line_track_ids.update({'carrier_id':carrier.id,
												'delivery_price':round(delivery_price,2),
												'is_vendor_track':True	
												})
			else:
				self.env['delivery.line.track'].sudo().create({
															'country_id':country_id,
															'order_id':order.id,
															'carrier_id':carrier.id,
															'delivery_price':round(delivery_price,2),
															'is_vendor_track':True
															})