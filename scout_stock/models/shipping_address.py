from odoo import api, models, fields, _

class SaleOrderShipping(models.Model):
	_inherit = 'sale.order'

	@api.onchange('partner_shipping_id')
	def partner_shipping_onchange(self):
		for order in self.order_line:
			if order.location_id:
				print("-------------------")
				if order.location_id.nso_location_id.country_id == self.partner_shipping_id.country_id:
					print("++++++++++++")
					# record = delivery_carr.search([('source_country_ids','=',self.partner_shipping_id.country_id.id)])
					# print('\n\n----------record--------',record)
					# return [('id','in',record)]
					# return [('delivery_method','in',record)]
					# return {'delivery_method':record.id}
					# return [('delivery_method','=',record)]
					# return {'domain':{'delivery_method':record.id}}
					# print("**************")
					return {'domain': {'delivery_method': [('source_country_ids','=',self.partner_shipping_id.country_id.id)]}}

	@api.multi
	def print_calcult(self,order):
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
				nso_line = order.order_line.filtered(lambda r:r.name == line.location_id.nso_location_id.name)

				if nso_line:
					nso_line.write({'price_unit':delivery_charge})
				else:
					vals = {
							'order_id':order.id,
							'name':line.location_id.nso_location_id.name,
							'product_id':delivery_product.id,
							'product_uom':delivery_product.sudo().uom_id.id,
							'price_unit':delivery_charge,
							'product_uom_qty':1.0,
							'is_nso_delivery_line':True
							}
					if delivery_charge > 0:
						sale_order_line_obj.create(vals)
