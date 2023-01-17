from odoo import api, fields, models, tools, _

class University(models.Model):
    _inherit = "res.partner"

    def name_get(self):
        name_array = []
        hierarchical_naming = self.env.context.get('path', True)
        
        for record in self:
            if hierarchical_naming and record.parent_id:
                node = record.parent_id
                name = record.name
                while node:
                    name = "%s / %s"%(node.name, name)
                    node= node.parent_id
                name_array.append((record.id,name))
            else:
                name_array.append((record.id, record.name))
        return name_array
        
    is_university = fields.Boolean("Is a university", default=False)

    description = fields.Html(string="Description", translate=True)

    children_count = fields.Integer(compute='_compute_children_count', string='ch count')

    tree_depth = fields.Integer(compute='_compute_tree_depth', string="Tree Depth")

    def _compute_children_count(self):
        self.children_count = len(self.child_ids)
    
    def _compute_tree_depth(self):
        depth = 1
        node = self.sudo().parent_id
        while node:
            depth +=1
            node = node.parent_id
        self.tree_depth = depth