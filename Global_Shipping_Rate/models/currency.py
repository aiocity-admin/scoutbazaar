from odoo import fields,models,_,api

class Currency(models.Model):
    _name = 'currency'
    _description = "Currency of all countries"
    
    name = fields.Char(string = 'Currency', required=True)
    currency_code = fields.Char(string = 'Currency Code', required=True)