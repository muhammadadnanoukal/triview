from collections import OrderedDict
from odoo import api, fields, models, tools


class Location(models.Model):
    _inherit = "stock.location"
    warehouse_id = fields.Many2one('stock.warehouse', compute='_compute_warehouse_id', store=True)

    @api.depends('warehouse_view_ids')
    def _compute_warehouse_id(self):
        warehouses = self.env['stock.warehouse'].search([('view_location_id', 'parent_of', self.ids)])
        view_by_wh = OrderedDict((wh.view_location_id.id, wh.id) for wh in warehouses)
        self.warehouse_id = False
        for loc in self:
            path = set(int(loc_id) for loc_id in loc.parent_path.split('/')[:-1])
            for view_location_id in view_by_wh:
                if view_location_id in path:
                    loc.warehouse_id = view_by_wh[view_location_id]
                    break


class StockMoveInOut(models.Model):
    _name = "stock.move.in.out"
    _order = "date"
    _auto = False
    product_id = fields.Many2one('product.product', string='Product name', readonly=True)
    location_id = fields.Many2one('stock.location', string='From', readonly=True)
    location_dest_id = fields.Many2one('stock.location', string='To ', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', related="location_id.warehouse_id")
    warehouse_dest_id = fields.Many2one('stock.warehouse', related="location_dest_id.warehouse_id")
    product_uom = fields.Many2one('uom.uom', string='UOM', readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking type', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    state = fields.Char(string='State', readonly=True)
    reference = fields.Char(string='Reference', readonly=True)
    date = fields.Datetime(string='Date', readonly=True)
    begin_qty = fields.Float(string='Beginning Balance', readonly=True)
    move_in = fields.Integer(string='In', readonly=True)
    move_out = fields.Integer(string='Out', readonly=True)
    end_qty = fields.Float(string='Ending Balance', readonly=True)

    def name_get(self):
        lst = []
        for v in self:
            nm = self.env['product.product'].browse(v.product_id).name_get()[0][1]
            lst.append((v.id, nm))
        return lst

    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, 'stock_move_in_out')
        self._cr.execute(""" CREATE VIEW stock_move_in_out AS (
      WITH b AS (
             SELECT 
                stock_move.id,
                stock_move.product_id,
                stock_move.location_id,
                stock_move.location_dest_id,
                stock_move.reference,
                stock_move.product_uom,
                stock_move.state,
                stock_move.picking_type_id,
                stock_move.company_id,
                stock_move.date,
                stock_location.usage as loc_from,
                stock_location.scrap_location,
                stock_location_1.usage as loc_to,
                stock_location_1.scrap_location as scrap_location_to,
                stock_move.product_uom_qty as product_qty,
                    CASE
                        WHEN stock_location.usage <> 'internal' AND stock_location_1.usage = 'internal' and stock_move.state='done'
    THEN 1
                        WHEN stock_location.usage = 'internal' AND stock_location_1.usage <> 'internal' and stock_move.state='done'

    THEN '-1'::integer
                        ELSE 0
                    END *stock_move.product_qty AS qty
               FROM  (stock_move INNER JOIN stock_location ON stock_move.location_id = stock_location.id)
    INNER JOIN stock_location AS stock_location_1 ON stock_move.location_dest_id = stock_location_1.id
            )
     SELECT b.id, 
        b.product_id,
        b.location_id,
        b.location_dest_id,
        b.picking_type_id,
        b.reference,
        b.product_uom,
        b.state,
        b.company_id,
        sum(b.qty) OVER w - b.qty AS begin_qty,
        b.date,
        case when (b.loc_to='internal') then b.product_qty else 0 end as move_in,
        case when (b.loc_from='internal') then b.product_qty else 0 end as move_out,
        sum(b.qty) OVER w AS end_qty
       FROM b
      WINDOW w AS (PARTITION BY b.product_id ORDER BY b.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      ORDER BY b.date

            )""")
