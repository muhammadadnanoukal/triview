from odoo import fields, api, models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
