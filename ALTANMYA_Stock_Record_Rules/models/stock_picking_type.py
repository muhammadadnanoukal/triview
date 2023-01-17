from odoo import fields, api, models

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    users_have_access = fields.Many2many('res.users', string='Users have access', domain=[('share', '=', False)])