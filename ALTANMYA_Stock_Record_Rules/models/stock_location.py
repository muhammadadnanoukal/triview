from odoo import fields, api, models

class Location(models.Model):
    _inherit = "stock.location"

    users_have_access = fields.Many2many('res.users', string='Users have access', domain=[('share', '=', False)])