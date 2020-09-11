
from odoo import fields,models,_,api

class ServiceableCountry(models.Model):

    _name = 'gb.serviceable_country'
    _description = 'Serviceable county contains all list of countries'
    
    name = fields.Char(string = 'Name', required=True)
    country_code = fields.Char(string = 'Country Code', required=True)
    is_active = fields.Boolean(string = "Covid status / service available or not") 