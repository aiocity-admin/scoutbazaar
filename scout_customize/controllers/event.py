# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from datetime import datetime
from odoo import http, tools, _
from odoo import api, models, fields, _
import logging
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.website_sale.controllers.main import WebsiteSale

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from werkzeug.exceptions import Forbidden
from odoo.addons.http_routing.models.ir_http import slug


class WebsiteEventController(WebsiteEventController):
    
    def sitemap_event(env, rule, qs):
        if not qs or qs.lower() in '/events':
            yield {'loc': '/events'}
    
    
    @http.route(['/event', '/event/page/<int:page>', '/events', '/events/page/<int:page>'], type='http', auth="public", website=True, sitemap=sitemap_event)
    def events(self, page=1, **searches):
        searches.setdefault('filter_event','my_events')
        res = super(WebsiteEventController,self).events(page,**searches)
        Event = request.env['event.event'].sudo()
        EventType = request.env['event.type'].sudo()
        dates = res.qcontext.get("dates")

        domain_search = {'website_specific': request.website.website_domain()}
        current_date = None
        current_type = None
        current_country = None
        events = Event.search([])

        def dom_without(without):
            Event = request.env['event.event'].sudo()
            domain = [('state', "in", ['draft', 'confirm', 'done']),('id' , 'in' ,events_new.ids)]
            for key, search in domain_search.items():
                if key != without:
                    domain += search
            return domain
        
        def dom_store(without):
            Event = request.env['event.event'].sudo()
            domain = [('state', "in", ['draft', 'confirm', 'done']),('id' , 'in' ,events_new.ids)]
            for key, search in domain_search.items():
                if key != without:
                    domain += search
            return domain
        
        if res.qcontext.get('searches').get('filter_event'):
            pager = res.qcontext.get('pager')
            step = 10   
            order = 'date_begin'
            if searches.get('date', 'all') == 'old':
                order = 'date_begin desc'
            order = 'is_published desc, ' + order
 
            events = Event.search([])

            events_new = request.env['event.event'].sudo()
            
            normal_events = request.env['event.event'].sudo().search([('troop_id' ,'=', False)])
            troop_events = request.env['event.event'].sudo().search([('troop_id' ,'!=', False)])
            troop_ids = request.env['troop.event'].sudo().search([('member_ids','in',[request.env.user.id])])                            
            troop_events_ids = Event.search([('troop_id','in',troop_ids.ids),('id','in',troop_events.ids)])
            events_new = normal_events + troop_events_ids
            current_date_filter = False
            date_filter = False

            for date in dates:
                if date[0] != 'old':
                    date[3] = Event.search_count(dom_without('date') + date[2] + [('id','in',events_new.ids)])
            if 'date' in searches:
                current_date_filter = searches.get('date')
            
            if current_date_filter:
                for date in dates:
                    if current_date_filter == date[0]:
                        date_filter = date[2] 

            if date_filter:
                date_filter.append(('id','in',events_new.ids))
                events_new = Event.search(date_filter)
            res.qcontext.update({'event_ids':events_new,'dates':dates})
        return res
    
    
    @http.route(['/event/<model("event.event"):event>/registration/new'], type='json', auth="public", methods=['POST'], website=True)
    def registration_new(self, event, **post):
        tickets = self._process_tickets_details(post)
        order = request.website.sale_get_order(force_create=True)
        if order and order.order_line:
            for line in order.order_line:
                    if line.event_ok:
                        if not tickets:
                            return False
                        return request.env['ir.ui.view'].render_template("website_event.registration_attendee_details", {'tickets': tickets, 'event': event})
                    else:
                        return request.env['ir.ui.view'].render_template('scout_customize.my_event_details')
        else:
            if not tickets:
                return False
            return request.env['ir.ui.view'].render_template("website_event.registration_attendee_details", {'tickets': tickets, 'event': event})
    
class WebsiteSaleSelecteEventOrder(WebsiteSale):
    
    #Orderline Event Filters======================================
    @http.route(['/check/event'], type='json', auth="public", website=True)
    def add_event(self, **post):
        order = request.website.sale_get_order()
        if order and order.order_line:
            for line in order.order_line:
                if line.event_ok:
                    return True
                else:
                    return False
        else:
            return False
