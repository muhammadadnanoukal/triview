# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import http, _
from odoo.http import request
from odoo.osv import expression
import os
import base64
import logging
import datetime
from dateutil.relativedelta import relativedelta

import werkzeug.datastructures
import werkzeug.exceptions
import werkzeug.local
import werkzeug.routing
import werkzeug.wrappers
from werkzeug import urls
from werkzeug.wsgi import wrap_file
from odoo.addons.http_routing.models.ir_http import slug

try:
    from werkzeug.middleware.shared_data import SharedDataMiddleware
except ImportError:
    from werkzeug.wsgi import SharedDataMiddleware

logger = logging.getLogger(__name__)

from odoo.addons.website.controllers.main import QueryURL

from odoo.osv.expression import AND, OR
from odoo.tools import groupby as groupbyelem

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class WebsiteDocument(portal.CustomerPortal):

    # util methods #################################################################################

    def binary_content(self, id, env=None, field='datas',
                       download=False, unique=False, filename_field='name'):
        env = env or request.env
        record = env['documents.document'].browse(int(id))
        filehash = None
        print("record", record, record.type, record.url)
        mimetype = False
        if record.type == 'url' and record.url:
            module_resource_path = record.url
            filename = os.path.basename(module_resource_path)
            status = 301
            content = module_resource_path
        else:
            status, content, filename, mimetype, filehash = env['ir.http']._binary_record_content(
                record, field=field, filename=None, filename_field=filename_field,
                default_mimetype='application/octet-stream')
        status, headers, content = env['ir.http']._binary_set_headers(
            status, content, filename, mimetype, unique, filehash=filehash, download=download)

        return status, headers, content

    def _get_file_response(self, id, field='datas'):
        """
        returns the http response to download one file.

        """

        status, headers, content = self.binary_content(
            id, field=field, download=True)

        if status != 200:
            return request.env['ir.http']._response_by_status(status, headers, content)
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)

        return response
    
    # single file download route.
    @http.route(["/document/download/<int:id>"],
                type='http', auth='public')
    def download_one(self, id=None, **kwargs):
        """
        used to download a single file from the portal multi-file page.

        :param id: id of the file
        :param access_token:  token of the share link
        :param share_id: id of the share link
        :return: a portal page to preview and download a single file.
        """
        try:
            document = self._get_file_response(id, field='datas')
            return document or request.not_found()
        except Exception:
            logger.exception("Failed to download document %s" % id)

        return request.not_found()
    
    @http.route(['/researches/view/<model("documents.document"):research>',], type='http', auth="public", website=True, sitemap=True)
    def document_view(self, research, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kwargs):
        
        query = werkzeug.urls.url_encode({
                    'redirect': '/researches/view/%s' % (slug(research),),
                })
        usr = request.env.user._is_public()
        values = ({
            'doc': research.sudo(),
            'page_name': 'home',
            'default_url': '/researches',
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'filterby': filterby,
            'public': usr,
            'btn_url': '/web/login?%s' %query if usr else '/document/download/%s'%research.id
        })

        return request.render('altanmia_researches_library.document_info',values)

    @http.route([
        '/researches',
        '/researches/page/<int:page>',
    ], type='http', auth='public', website=True)
    def portal_researches(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kwargs):
        values = self._prepare_portal_layout_values()
        research = request.env['documents.document'].sudo()

        domain = self._get_portal_default_domain()

        searchbar_sortings = {
            'create_date': {'label': _('Date'), 'order': 'create_date'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        searchbar_inputs = {
            'all': {'label': _('Search in All'), 'input': 'all'},
            'name': {'label': _('Search in Name'), 'input': 'name'},
            'keyword': {'label': _('Search in Keywords'), 'input': 'keyword'},
            'abstract': {'label': _('Search in Abstract'), 'input': 'abstract'}
        }

        searchbar_filters = {
            # 'university': {'label': _("Upcoming"), 'domain': [('start', '>=', datetime.today())]},
            # 'past': {'label': _("Past"), 'domain': [('start', '<', datetime.today())]},
            'all': {'label': _("All"), 'domain': []},
            'phd': {'label': _('PHD'), 'domain':[('research_degree', '=', 'phd')]},
            'master': {'label': _('Master'), 'domain':[('research_degree', '=', 'master')]},
            'year_ago': {'label': _('This Year'), 'domain':[('create_date', '>=', datetime.datetime.today() - datetime.timedelta(days=365))]},
        }

        if not sortby:
            sortby = 'create_date'
        sort_order = searchbar_sortings[sortby]['order']

        order =  sort_order

        if not filterby:
            filterby = 'all'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        if search and search_in:
            domain = AND([domain, self._get_research_search_domain(search_in, search)])

        research_count = research.search_count(domain)
        pager = portal_pager(
            url="/researches",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby},
            total=research_count,
            page=page,
            step=self._items_per_page
        )
        researches = research.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        keep = QueryURL('/researches', [sortby, filterby, search, search_in, groupby])



        values.update({
            'researches': researches,
            'page_name': 'home',
            'pager': pager,
            'default_url': '/researches',
            'searchbar_sortings': searchbar_sortings,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'keep': keep,
            'groupby': groupby,
            'filterby': filterby,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_filters': searchbar_filters,

        })
        return request.render("altanmia_researches_library.document_list_layout", values)
    
    def _get_research_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('all', 'name'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        if search_in in ('all', 'abstract'):
            search_domain = OR([search_domain, [('abstract', 'ilike', search)]])
        if search_in in ('all', 'keyword'):
            search_domain = OR([search_domain, [('keyword_ids.name', 'ilike', search)]])
        return search_domain
    
    def _get_portal_default_domain(self):
        return [
            ('is_research', '=', True),
            ('is_published', '=', True),
        ]

    @http.route(['/researches/search_fileds'], type="json", auth="public", website=True, sitemap=False)
    def get_fields(self):
        fields =  [
            { 'string': "ID", 'type': "id", 'name': "id" },
            { 'string': "Name", 'type': "char", 'name': "name" },
            {'string': "Created at", 'type': "date", 'name':'create_date'},
            { 'string': "Abstract", 'type': "char", 'name': "abstract" },
            { 'string': "keywords", 'type': "many2many", 'name': "keyword_ids" },
            { 'string': "Specialization", 'type': "many2one", 'name': "related_id" },
            { 'string': "College", 'type': "many2one", 'name': "related_id.parent_id" },
            { 'string': "University", 'type': "many2one", 'name': "related_id.parent_id.parent_id" },
            { 'string': "Degree", 'type': "selection", 'name': "research_degree" , 'selection':[('phd', 'PHD'),('master', 'Master'),('other','Other')]}
        ]
        return  fields
    
    @http.route(['/researches/custom_filter'], type="json", auth="public", website=True, sitemap=False)
    def research_filter(self, conditions):
        domain = self._get_portal_default_domain()
        for cnd in conditions:
            if len(cnd['or_conditions'])>0:
                andDomain = []
                for d in cnd['domain']:
                    andDomain = AND([andDomain, [tuple(d)]])
                orDomain = andDomain
                for orD in cnd['or_conditions']:
                    andDomain = []
                    for d in orD['domain']:
                        andDomain = AND([andDomain,[tuple(d)] ])
                    orDomain = OR([orDomain,andDomain])

                domain = AND([domain,orDomain])
            else:
                for d in cnd['domain']:
                   domain =  AND([domain, [tuple(d)] ])

        research = request.env['documents.document'].sudo()
        researches = research.search(domain, order='create_date', limit=50)
        keep = QueryURL('/researches', [None, None, None, 'all', 'none'])
        result = request.env['ir.ui.view']._render_template("altanmia_researches_library.researches_list", {
                'researches': researches,
                'keep': keep,
            })
        logger.info("custom filter domain %s"%domain)
        return result
        

        

