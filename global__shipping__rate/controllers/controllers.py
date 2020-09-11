# -*- coding: utf-8 -*-
from odoo import http


class GlobalShippingRate(http.Controller):
    @http.route('/global__shipping__rate/global__shipping__rate/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/global__shipping__rate/global__shipping__rate/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('global__shipping__rate.listing', {
            'root': '/global__shipping__rate/global__shipping__rate',
            'objects': http.request.env['global__shipping__rate.global__shipping__rate'].search([]),
        })

    @http.route('/global__shipping__rate/global__shipping__rate/objects/<model("global__shipping__rate.global__shipping__rate"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('global__shipping__rate.object', {
            'object': obj
        })
