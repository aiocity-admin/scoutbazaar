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
from odoo.exceptions import UserError, ValidationError

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id','country_id','town_id','district_id','city_id')

class ResPartner(models.Model):
    
    
    _inherit = 'res.partner'
    
    country_code = fields.Char('Country Code',related='country_id.code')
    city_id = fields.Many2one('res.partner.city',string="Province")
    district_id = fields.Many2one('res.partner.district',string='City / Municipality')
    town_id = fields.Many2one('res.partner.town',string='Barangay')
    
    @api.multi
    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        if self.country_id.code == 'PH':
            address_format = '%(street)s, %(town_id_name)s\n%(district_id_name)s, %(city_id_name)s, %(zip)s\n%(country_name)s'
            args = {
                'town_id_name': self.town_id.name or '',
                'district_id_name': self.district_id.name or '',
                'city_id_name': self.city_id.name or '',
                'state_code': self.state_id.code or '',
                'state_name': self.state_id.name or '',
                'country_code': self.country_id.code or '',
                'country_name': self._get_country_name(),
                'company_name': self.commercial_company_name or '',
            }
            for field in self._formatting_address_fields():
                args[field] = getattr(self, field) or ''
            if without_company:
                args['company_name'] = ''
            elif self.commercial_company_name:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args
        else:
            address_format = self._get_address_format()
            args = {
                'state_code': self.state_id.code or '',
                'state_name': self.state_id.name or '',
                'country_code': self.country_id.code or '',
                'country_name': self._get_country_name(),
                'company_name': self.commercial_company_name or '',
            }
            for field in self._formatting_address_fields():
                args[field] = getattr(self, field) or ''
            if without_company:
                args['company_name'] = ''
            elif self.commercial_company_name:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args
    @api.onchange('city_id')
    def onchange_city(self):
        
        district_list = []
        city_id = self.city_id and self.city_id.id or False
        
        if self.country_id.code == 'PH':
            self.city = self.city_id.name
            if self.town_id and self.city_id and self.district_id:
                servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                              ('town_id','=',int(self.town_id)),
                                                              ('city_id','=',int(self.city_id)),
                                                              ('district_id','=',int(self.district_id)),
                                                              ],limit=1)
                if servicable_area:
                    self.state_id = servicable_area.state_id.id

            if city_id:
                servicable_area = self.env['jt.servicable.areas'].sudo().search([('city_id','=',int(city_id))])
                for ids in servicable_area:
                    if not ids.district_id.id in district_list:
                        district_list.append(ids.district_id.id)
                return {'domain': {'district_id': [('id','in',district_list)]}}
    
    @api.onchange('district_id')
    def onchange_district(self):

        town_list = []
        district_id = self.district_id.id
        
        if self.country_id.code == 'PH':
            if self.town_id and self.city_id and self.district_id:

                servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                              ('town_id','=',int(self.town_id)),
                                                              ('city_id','=',int(self.city_id)),
                                                              ('district_id','=',int(self.district_id)),
                                                              ],limit=1)
                if servicable_area:
                    self.state_id = servicable_area.state_id.id
                    
            if self.city_id and self.city_id.id:
                if district_id:
                    servicable_area = self.env['jt.servicable.areas'].sudo().search([('district_id','=',int(district_id))])
                    for ids in servicable_area:
                        if not ids.town_id.id in town_list:
                            town_list.append(ids.town_id.id)
                    return {'domain': {'town_id': [('id','in',town_list)]}}
            else:
                raise ValidationError(_("Please Select Province!"))
        
    @api.onchange('town_id')
    def onchange_town(self):

        if self.country_id.code == 'PH':
            if self.town_id and self.city_id and self.district_id:
                servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                              ('town_id','=',int(self.town_id)),
                                                              ('city_id','=',int(self.city_id)),
                                                              ('district_id','=',int(self.district_id)),
                                                              ],limit=1)
                if servicable_area:
                    self.state_id = servicable_area.state_id.id

            
            if not self.district_id and not self.city_id:
                raise ValidationError(_("Please Select Province!"))

            if not self.district_id:
                raise ValidationError(_("Please Select City / Municipality !"))  

    @api.multi
    def write(self,values):
        
        if self._context.get('website_id'):
            for res in self:
                #Parent code==============
                if 'country_id' in values: 
                    country = self.env['res.country'].sudo().search([('id','=', values.get('country_id'))])
                    if country.code == 'PH':
                        town_id = False
                        district_id = False
                        city_id = False
                        if 'town_id' in values:
                            town_id = values.get('town_id')
                             
                        else:
                            town_id = res.town_id.id
                                  
                        if 'district_id' in values:
                            district_id = values.get('district_id')
                        else:
                            district_id = res.district_id.id
                                  
                                  
                        if 'city_id' in values:
                            city_id = values.get('city_id')
                        else:
                            city_id = res.city_id.id
                          
                        if town_id and district_id and city_id:
                            servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                                                      ('town_id','=',int(town_id)),
                                                                                      ('city_id','=',int(city_id)),
                                                                                      ('district_id','=',int(district_id)),
                                                                                      ],limit=1)
                            if servicable_area:
                                values.update({'state_id':servicable_area.state_id.id})
                            else:
                                values.update({'state_id':False})
                 
                
                elif 'town_id' in values or 'district_id' in values or 'city_id' in values:
                    if res.country_id.code == 'PH':
                        town_id = False
                        district_id = False
                        city_id = False
                        if 'town_id' in values:
                            town_id = values.get('town_id')
                        else:
                            town_id = res.town_id.id
                                  
                        if 'district_id' in values:
                            district_id = values.get('district_id')
                        else:
                            district_id = res.district_id.id        
                                  
                        if 'city_id' in values:
                            city_id = values.get('city_id')
                        else:
                            city_id = res.city_id.id
                             
                        if town_id and district_id and city_id:
                            servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                                                      ('town_id','=',int(town_id)),
                                                                                      ('city_id','=',int(city_id)),
                                                                                      ('district_id','=',int(district_id)),
                                                                                      ],limit=1)
                            if servicable_area:
                                values.update({'state_id':servicable_area.state_id.id})
                            else:
                                values.update({'state_id':False})
             
        return super(ResPartner,self).write(values)
    
    
    
    @api.model
    def create(self,vals):
        country_code = False
        if 'country_id' in vals:
            res_country = self.env['res.country'].sudo().browse(int(vals.get('country_id')))
            if res_country:
                country_code = res_country.code
        if self.country_id.code == 'PH' or country_code == 'PH':
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
                if self.city_id and self.city_id.id:
                    city_id = self.city_id.id
            
            if town_id and district_id and city_id:
                servicable_area = self.env['jt.servicable.areas'].sudo().search([
                                                                          ('town_id','=',int(town_id)),
                                                                          ('city_id','=',int(city_id)),
                                                                          ('district_id','=',int(district_id)),
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
    