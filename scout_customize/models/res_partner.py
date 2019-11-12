# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _


class Respartner(models.Model):

    _inherit = 'res.partner'
    
    school_list_ids = fields.Many2many("school.list" ,string="School")
    
    boy_scout =fields.Selection([('cub_scout','Cub Scout '),
                                               ('boy_scout','Boy Scout')],string='Boy Scout',)
    
    scout_user_rank =fields.Selection([('cub','Cub'),
                                          ('scout','Scout'),
                                          ('den_master','Den Master '),
                                          ('scout_master','Scout Master'),
                                          ('patrol_leader','Patrol Leader'),
                                          ('troop_leader','Troop Leader ')
                                          ],string='Boy/Girl Scout User Rank',)
    
  