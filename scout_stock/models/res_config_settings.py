from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ResConfigSettings(models.TransientModel):
    
    
    _inherit = 'res.config.settings'
    
    handling_charge = fields.Float(string="Shipping Handling Charge")
    payment_processing_fee = fields.Float(string="Acquirer Processing Fee")
    transaction_value = fields.Float(string="Transaction Value")

    @api.model
    def default_get(self,fields):
        settings = super(ResConfigSettings,self).default_get(fields)
        settings.update(self.get_payment_handling_value(fields))
        return settings
    
    @api.model
    def get_payment_handling_value(self, fields):
        handling_config= self.env.ref('scout_stock.handling_fees_config')
        return {
                'payment_processing_fee': handling_config.payment_processing_fee,
                'transaction_value': handling_config.transaction_value,
                'handling_charge':handling_config.handling_charge,
                }
    
    @api.multi
    def set_values(self):
        handling_config= self.env.ref('scout_stock.handling_fees_config')
        handling_config.sudo().write({
                                'payment_processing_fee': self.payment_processing_fee,
                                'transaction_value': self.transaction_value,
                                'handling_charge':self.handling_charge,
                                 })
        return super(ResConfigSettings, self).set_values()


class ResConfigSettingsFees(models.Model):
    
    _name = 'payment.handling.config'
    
    handling_charge = fields.Float(string="Shipping Handling Charge")
    payment_processing_fee = fields.Float(string="Acquirer Processing Fee")
    transaction_value = fields.Float(string="Transaction Value")
    