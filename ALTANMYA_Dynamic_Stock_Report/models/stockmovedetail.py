from odoo import api, fields, models, tools

class StockMoveDetails(models.Model):
    _name = "stock.move.detail"
    _order = "date"
    _auto = False
    product_id = fields.Many2one('product.product', string='Product name', readonly=True)
    location_id = fields.Many2one('stock.location', string='From', readonly=True)
    location_dest_id = fields.Many2one('stock.location', string='To ', readonly=True)
    product_packaging_id = fields.Many2one('product.packaging', string='Packaging Id', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', related="location_id.warehouse_id")
    warehouse_dest_id = fields.Many2one('stock.warehouse', related="location_dest_id.warehouse_id")
    product_uom = fields.Many2one('uom.uom',string='UOM', readonly=True)
    picking_type_id=fields.Many2one('stock.picking.type', string='Picking type', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    state = fields.Char(string='State', readonly=True)
    reference = fields.Char(string='Reference', readonly=True)
    date = fields.Datetime(string='Date', readonly=True)
    begin_qty = fields.Float(string='Begining Balance', readonly=True)
    purchased = fields.Float(string='Purchased', readonly=True)
    manufactured = fields.Float(string='Manufactured ', readonly=True)
    senttoproduction = fields.Float(string='Sent to production', readonly=True)
    scrap = fields.Float(string='Scrap')
    adjustement = fields.Float(string='Adjustement', readonly=True)
    transfered = fields.Float(string='Transfered', readonly=True)
    sold = fields.Float(string='Sold', readonly=True)
    end_qty = fields.Float(string='Ending Balance', readonly=True)

    def name_get(self):
        lst = []
        for v in self:
            nm = self.env['product.product'].browse(v.product_id).name_get()[0][1]
            lst.append((v.id, nm))
        return lst

    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, 'stock_move_detail')
        self._cr.execute(""" CREATE VIEW stock_move_detail AS (
      WITH b AS (
             SELECT 
                stock_move.id,
                stock_move.product_id,
                stock_move.location_id,
                stock_move.location_dest_id,
                stock_move.product_packaging_id,
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
        b.product_packaging_id,
        b.picking_type_id,
        b.reference,
        b.product_uom,
        b.state,
        b.company_id,
        sum(b.qty) OVER w - b.qty AS begin_qty,
        b.date,
        case when (b.loc_from='supplier' and b.loc_to='internal') or (b.loc_from='internal' and b.loc_to='supplier') then b.qty else 0 end as purchased,
        case when b.loc_from='production' and b.loc_to='internal' then b.qty else 0 end as manufactured,
        case when b.loc_from='internal' and b.loc_to='production' then -1*b.qty else 0 end as senttoproduction,
        case when b.scrap_location_to and b.loc_to='inventory' then -1*b.qty else 0 end as scrap,
        case when (not b.scrap_location and b.loc_from='inventory') or (not b.scrap_location_to and b.loc_to='inventory')  then b.qty else 0 end as adjustement,
        case when b.loc_from='internal' and b.loc_to='internal' then b.product_qty else 0 end as transfered,
        case when (b.loc_from='internal' and b.loc_to='customer') or (b.loc_from='customer' and b.loc_to='internal') then -1*b.qty else 0 end as sold,
        sum(b.qty) OVER w AS end_qty
       FROM b
      WINDOW w AS (PARTITION BY b.product_id ORDER BY b.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      ORDER BY b.date

            )""")