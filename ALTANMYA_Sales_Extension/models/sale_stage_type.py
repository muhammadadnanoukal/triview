from odoo import api, fields, models, tools


class TanmyaSaleStageType(models.Model):
    _name = "tanmya.sale.stage.type"
    name = fields.Char(string='Sale template', required=True)
    stages = fields.One2many('tanmya.sale.stage', 'sale_template', string='stages')
    currency = fields.Many2one('res.currency', string='Currency', required=False)
    minrange=fields.Float('From')
    maxrange=fields.Float('To')

    def get_stage_list(self):
        lst=[]
        for rec in self.stages:
            lst.append(rec.code)
        return lst
