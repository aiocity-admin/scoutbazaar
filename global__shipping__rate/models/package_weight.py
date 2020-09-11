
from odoo import fields,models,_,api

class PackageWeight(models.Model):

    _name = 'gb.package_weight'
    _description = 'Package weight contains total weight range of package'
    
    min_weight = fields.Float('Minimum Weight', required=True)
    max_weight = fields.Float('Maximum Weight', required=True)
    unit = fields.Char(string = 'Unit(Gram/KG)', required=True)
    name = fields.Char(string = 'Name',compute="_compute_name")


    @api.multi
    @api.depends('min_weight','max_weight','unit')
    def _compute_name(self):
        for ship_id in self:
            if ship_id.state_id and ship_id.origin_id:
                ship_id.name = ship_id.origin_id.name + '-' + ship_id.state_id.name + '(' + str(ship_id.min_weight) + '-' +  str(ship_id.max_weight) + ')'
