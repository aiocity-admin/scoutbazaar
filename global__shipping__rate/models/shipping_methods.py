
from odoo import fields,models,_,api

class ShippingMethods(models.Model):

    _name = 'gb.shipping_methods'
    _description = 'Contains shipping types'
    
    name = fields.Char(string = 'Name', required=True)
    shipping_code = fields.Char(string = 'Shipping Code', required=True)