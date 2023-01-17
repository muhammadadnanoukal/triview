import base64

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource
from odoo.addons.http_routing.models.ir_http import slug
from odoo.osv import expression
from collections import OrderedDict


class Folder(models.Model):
    _name= 'documents.folder'

    _inherit = [
        'portal.mixin','documents.folder',
        'website.seo.metadata',
        'website.published.mixin',
    ]

    is_published = fields.Boolean(
        string='Published to Wibsite', default=False,  # force None to avoid default computation from mixin
        readonly=False, store=True, help='Publish this workspace and all sub workspace content to website')
    is_research = fields.Boolean(string='Is Document Research', default=False)


    def _compute_website_url(self):
        super(Folder, self)._compute_website_url()
        for folder in self:
            if folder.id:
                folder.website_url = '/researches/view/%s' % (slug(folder),)
            else:
                folder.website_url = False

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Force False manually for all categories of appointment type when duplicating
        even for categories that should be auto-publish. """
        default = default if default is not None else {}
        default['is_published'] = False
        return super().copy(default)

class Document(models.Model):
    _name= 'documents.document'

    _inherit = [
        'portal.mixin','documents.document',
        'website.seo.metadata',
        'website.published.mixin',
    ]

    is_published = fields.Boolean(
        string='Published to Wibsite', default=False,  # force None to avoid default computation from mixin
        readonly=False, store=True, help='Publish this file to wibsite')

    is_research = fields.Boolean(string='Is Document Research', default=False)

    research_degree = fields.Selection(([('phd', 'PHD'),('master', 'Master'),('other','Other')]), string="Degree" , default='other')

    related_id  = fields.Many2one('res.partner', string='Related To', index=True, required=True)
    arbitration_ids = fields.One2many('researches.arbitration', 'research_id', string="Arbitrations")

    keyword_ids = fields.Many2many('researches.keyword', 'researches_keyword_rel', string="Keywords")
    abstract = fields.Html("Abstract")

    reference_college = fields.Char(compute="_compute_college_deparmant_name")
    university = fields.Char(compute="_compute_university_name")

    def _get_image_holder(self):
        """Returns the holder of the image to use as default representation.
        """
        self.ensure_one()
        university = self.sudo().related_id
        while university.tree_depth > 1:
            university = university.parent_id
        return university if university and university.image_128 else False

    def _compute_college_deparmant_name(self):
        for rec in self:
            node = rec.related_id
            name=''
            while node and node.tree_depth>1:
                name = "%s / %s"%(node.name, name)
                node= node.parent_id
            rec.reference_college = name
    
    def _compute_university_name(self):
        for rec in self:
            node = rec.related_id
            name=''
            while node and node.tree_depth>1:
                node= node.parent_id
            
            rec.university = node.name if node else ''

    def _compute_website_url(self):
        super(Document, self)._compute_website_url()
        for doc in self:
            if doc.id:
                doc.website_url = '/researches/view/%s' % (slug(doc),)
            else:
                doc.website_url = False

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Force False manually for all categories of appointment type when duplicating
        even for categories that should be auto-publish. """
        default = default if default is not None else {}
        default['is_published'] = False
        return super().copy(default)
    
    @api.model
    def create(self, vals):
        folder = self.env['documents.folder'].search([('is_research','=',True)],limit=1)
        if not folder:
            folder = self.env['documents.folder'].create({'name':'Researches Folder', 'is_research':True})
        
        vals['folder_id'] = folder.id

        return super().create(vals)

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        
        if field_name == 'related_id':
            enable_counters = kwargs.get('enable_counters', False)
            fields = ['name', 'description', 'parent_id']
            available_folders = self.env['res.partner'].search([])
            folder_domain = [('is_university', '=', True),'|',('parent_id', 'parent_of', available_folders.ids), ('id', 'in', available_folders.ids)]
            
            # also fetches the ancestors of the available folders to display the complete folder tree for all available folders.
            DocumentFolder = self.env['res.partner'].sudo().with_context(path=False)
            records = DocumentFolder.search_read(folder_domain, fields)

            domain_image = {}
            if enable_counters:
                model_domain = expression.AND([
                    kwargs.get('search_domain', []),
                    kwargs.get('category_domain', []),
                    kwargs.get('filter_domain', []),
                    [(field_name, '!=', False)]
                ])
                domain_image = self._search_panel_domain_image(field_name, model_domain, enable_counters)

            values_range = OrderedDict()
            for record in records:
                record_id = record['id']
                if enable_counters:
                    image_element  = domain_image.get(record_id)
                    record['__count'] = image_element['__count'] if image_element else 0
                value = record['parent_id']
                record['parent_id'] = value and value[0]
                record['display_name'] = record['name']
                values_range[record_id] = record

            if enable_counters:
                self._search_panel_global_counters(values_range, 'parent_id')
            return {
                'parent_field': 'parent_id',
                'values': list(values_range.values()),
            }

        return super(Document, self).search_panel_select_range(field_name)

class Arbitration(models.Model):

    _name="researches.arbitration"
    _description = 'Research arbitration'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _order = 'id desc'

    arbitrator = fields.Many2one('res.partner', string='Arbitrator', index=True, required=True)
    research_id = fields.Many2one('documents.document', string='Research', index=True, required=True)

    rate = fields.Float("Rate")

    opinion = fields.Html("Arbitrator Opinion")

KEYWORD_COLORS = ['#F06050', '#6CC1ED', '#F7CD1F', '#814968', '#30C381', '#D6145F', '#475577', '#F4A460',
                          '#EB7E7F', '#2C8397', '#FA6050', '#6CF1ED', '#F0CD1F', '#81D96A', '#30C38A', '#D614FF', '#875577', '#F4A46F',
                          '#EB7E0F', '#AC8397']

class ResearchesKeyword(models.Model):
    _name = "researches.keyword"
    _description = "Researches keyword"

    

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer(string="Color")
    color_2 = fields.Char(string="Color")
    hex_color = fields.Char(compute='_compute_hex_color')

    def _compute_hex_color(self):
        for rec in self:
            rec.hex_color = KEYWORD_COLORS[rec.color] if rec.color < len(KEYWORD_COLORS) else '#FF4587'

    



