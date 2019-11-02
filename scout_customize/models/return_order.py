from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from odoo.addons import decimal_precision as dp

class ReturnSaleOrder(models.Model):
    
    _name = 'return.order'

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()
    
    name = fields.Char(string='Return Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('return', 'Return'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    picking_id = fields.Many2one('stock.picking', domain="[('sale_id', '=', sale_order_id)]", string="Delivery Order")
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_delivery_order')
    Picking_count = fields.Integer(string='Order Picking', compute='_compute_return_picking')

    partner_id = fields.Many2one('res.partner',string='Customer',help="You can find a customer by its Name, TIN, Email or Internal Reference.")
    sale_order_id = fields.Many2one('sale.order',required=True , domain="[('picking_ids', '!=', False)]", string='Sale Order', help="sale for current sales order.")
    create_order_date = fields.Datetime(string='Create Date', default=fields.Datetime.now)
    order_customer = fields.Many2one(readonly=True,related='sale_order_id.partner_id', string='Customer',help="You can find a customer by its Name, TIN, Email or Internal Reference.")
    sale_order_line = fields.Many2one('sale.order.line',required=True ,string='Order line', help="sale for current sales order.")
    return_product = fields.Many2one(readonly=True,related='sale_order_line.product_id', string='Return Product')
    return_qty = fields.Float(readonly=True,string='Return Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    product_uom = fields.Many2one(related='sale_order_line.product_uom', string='Unit of Measure',readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=_get_default_team, oldname='section_id')
    note = fields.Text('Reason of Return')
    delivery_order_lines = fields.One2many('stock.picking','rma_id', string='Delivery Order')
    return_picking_line = fields.One2many('stock.picking','rma_id_picking', string='Picking Order')
    
    @api.onchange('sale_order_id')
    def onchange_order_id(self):
        if self.sale_order_id:
            self.sale_order_line =False
            sale_order = self.env['sale.order'].search([])
            return {'domain': {'sale_order_line': [('id','in',self.sale_order_id.order_line.ids)]}}
        else:
            return {'domain': {'sale_order_line': [('id','in',[])]}}
    
    @api.depends('return_picking_line')
    def _compute_return_picking(self):
        for order in self:
            order.Picking_count = len(order.return_picking_line)
    
    @api.depends('delivery_order_lines')
    def _compute_delivery_order(self):
        for order in self:
            order.delivery_count = len(order.delivery_order_lines)
    
    @api.model
    def create(self,vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('return.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('return.order') or _('New')
        result = super(ReturnSaleOrder, self).create(vals)
        return result
    
    @api.multi
    def rmo_action_confirm(self):
        self.write({
            'state': 'confirmed',
        })
        list=[]
        for ids in self.sale_order_id.picking_ids:
            if ids.location_id == self.sale_order_line.location_id and ids.picking_type_id.code == 'outgoing':
                if ids.state == 'done':
                    list.append(ids.id)
        if list:
            self.write({'delivery_order_lines':[(6, 0, list)]})
        else:
            raise UserError(_('your sale order stock.picking id is not done'))
        for delivery_line in self.delivery_order_lines:
            if delivery_line.location_id == self.sale_order_line.location_id and delivery_line.picking_type_id.code == 'outgoing':
                delivery_line.write({'rma_order_ref': [(4,self.id,False)]})
    
    @api.multi
    def rmo_action_cancel(self):
        return self.write({'state': 'cancel'})
    
    @api.multi
    def rmo_action_return(self):
        list=[]
        list_picking=[]
        return_picking_line = False
        for ids in self.delivery_order_lines:
            if ids.picking_type_id.code == 'incoming':
#                 if ids.state == 'done':
                list.append(ids.id)
            if ids.picking_type_id.code == 'outgoing':
                list_picking.append(ids.id)
        if list_picking:
            self.write({'delivery_order_lines':[(6, 0, list_picking)]})
        if list:
            self.write({'return_picking_line':[(6, 0, list)]})
        else:
            raise UserError(_('You have not recorded done quantities'))
        for picking_line in self.return_picking_line:
            picking_line.rma_order_ref = False
        return self.write({'state': 'return'})
    
    @api.multi
    def action_view_delivery_order(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('delivery_order_lines')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action
    
    @api.multi
    def action_view_delivery_picking(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('return_picking_line')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action
    
class stockpicking(models.Model):
    
    _inherit = 'stock.picking'
    
    rma_order_ref = fields.Many2many('return.order',string='RMA Order')
    rma_id = fields.Char('RMA')
    rma_id_picking = fields.Char('RMA picking')
    
    
class ReturnPickingReturns(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    @api.model
    def default_get(self, fields):
        res = super(ReturnPickingReturns, self).default_get(fields)
        ids = self.env['stock.picking'].search([('id','=',res['picking_id'])])
        
        if ids.rma_order_ref and 'product_return_moves' in res:
            if ids.rma_id:
                return_id = self.env['return.order'].search([('id','=',ids.rma_id)])
                move_id=False
                for mv_id in res['product_return_moves']:
                    if mv_id[2]['product_id'] == return_id.return_product.id:
                        move_id = mv_id[2]['move_id']
                res.update({'product_return_moves': [(0, 0, {'move_id':move_id,'quantity': return_id.return_qty, 'product_id': return_id.return_product.id, 'uom_id': return_id.product_uom.id})]})
        return res
    