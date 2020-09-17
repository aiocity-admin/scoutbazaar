# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StudentStudent(models.Model):
	_name = 'student'

	name = fields.Char(string='Name', compute='_compute_name')
	age = fields.Integer(string='Age')
	photo = fields.Binary(string='Image')
	gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('others', 'Others')], string='Gender')
	student_dob = fields.Date(string="Date of Birth")
	student_blood_group = fields.Selection(
		[('A+', 'A+ve'), ('B+', 'B+ve'), ('O+', 'O+ve'), ('AB+', 'AB+ve'),
    	('A-', 'A-ve'), ('B-', 'B-ve'), ('O-', 'O-ve'), ('AB-', 'AB-ve')],
    	string='Blood Group')
	nationality = fields.Many2one('res.country', string='Nationality')

	@api.depends('name')
	def _compute_name(self):
		for record in self:
			self.name = "Your age is %s" % self.age