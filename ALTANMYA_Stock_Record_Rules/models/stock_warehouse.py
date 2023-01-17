from odoo import fields, api, models

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    users_have_access = fields.Many2many('res.users', string='Users have access', domain=[('share', '=', False)])
