# -*- coding: utf-8 -*-

from odoo import models, fields, api


class global__shipping__rate(models.Model):
    _name = 'global__shipping__rate.global__shipping__rate'
    _description = 'global__shipping__rate.global__shipping__rate'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100
