# -*- coding: utf-8 -*-
from odoo import http

class MyModule(http.Controller):
    @http.route('/student/student/', auth='public')
    def index(self, **kw):
        Students = http.request.env['student']
        source_country = 'india'
        destination_country = 'Hong Kong'
        package_weight = '0-250'
        error_msg = ''
        values = {
            'students': Students.search([]),
            'countries':http.request.env['res.country'].search([]),
            'source_country':source_country,
            'destination_country':destination_country,
            'package_weight':package_weight
        }
        #response = http.request.render("portal.portal_my_details", values)
        return http.request.render('student.new_web_page', values)
        # return http.request.render('student.new_web_page', {
        #     'teachers': ["Diana Padilla", "Jody Caroll", "Lester Vaughn"],
        # })

    @http.route('/student/student/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('student.listing', {
            'root': '/student/student',
            'objects': http.request.env['student'].search([]),
        })

    @http.route('/student/student/objects/<model("student"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('student.object', {
            'object': obj
        })