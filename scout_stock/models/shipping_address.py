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
