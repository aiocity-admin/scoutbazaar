# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import models,fields,_,api
ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id','town_id','district_id','city_id')

class ResPartner(models.Model):
    
    
    _inherit = 'res.partner'
    
    
    country_code = fields.Char('Country Code',related='country_id.code')
    city_id = fields.Many2one('res.partner.city',string="Province")
    district_id = fields.Many2one('res.partner.district',string='City / Municipality')
    town_id = fields.Many2one('res.partner.town',string='Barangay')
#     territories_id = fields.Many2one('res.partner.territories', string="Territories")
#     name_building = fields.Char('Name of Building')
    
    
    @api.multi
    def write(self,values):
        for res_id in self:
            if res_id.country_id.code == 'PH':
                town_id = False
                district_id = False
                city_id = False
                print('===========res values=======================',values)
                if 'town_id' in values:
                    town_id = values.get('town_id')
                else:
                    if res_id.town_id.id:
                        town_id = res_id.town_id.id
                        
                if 'district_id' in values:
                    district_id = values.get('district_id')
                else:
                    if res_id.district_id.id:
                        district_id = res_id.district_id.id
                        
                        
                if 'city_id' in values:
                    city_id = values.get('city_id')
                else:
                    if res_id.city_id.id:
                        city_id = res_id.city_id.id
                
                
                print("Town id=============",town_id,district_id,city_id)
                if town_id and district_id and city_id:
                    servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                                              ('town_id','=',int(town_id)),
                                                                              ('city_id','=',int(city_id)),
                                                                              ('district_id','=',int(district_id)),
                                                                              ],limit=1)
                    print('=======servicable_area==================',servicable_area)
                    if servicable_area:
                        values.update({'state_id':servicable_area.state_id.id})
                    else:
                        res_id.update({'state_id':False})
            
        return super(ResPartner,self).write(values)
    
    
    
    @api.model
    def create(self,vals):
        if self.country_id.code == 'PH':
            town_id = False
            district_id = False
            city_id = False
            
            if 'town_id' in vals:
                town_id = vals.get('town_id')
            else:
                if self.town_id.id:
                    town_id = self.town_id.id
                    
            if 'district_id' in vals:
                district_id = vals.get('district_id')
            else:
                if self.district_id.id:
                    district_id = self.district_id.id
                    
                    
            if 'city_id' in vals:
                city_id = vals.get('city_id')
            else:
                if self.city_id.id:
                    city_id = self.city_id.id
            
            
            if town_id and district_id and city_id:
                servicable_area = self.env['jt.servicable.areas'].search([
                                                                          ('town_id','=',town_id),
                                                                          ('city_id','=',city_id),
                                                                          ('district_id','=',district_id),
                                                                          ],limit=1)
                
                if servicable_area:
                   
                    vals.update({'state_id':servicable_area.state_id.id})
                else:
                    vals.update({'state_id':False})
            
        return super(ResPartner,self).create(vals)
    
    
    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)
    