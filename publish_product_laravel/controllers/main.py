# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import http, _
from odoo.http import request
import logging
import json
from odoo.addons.http_routing.models.ir_http import slug

logger = logging.getLogger(__name__)

from odoo.addons.portal.controllers import portal
from odoo.exceptions import UserError


class ProductPublisher(portal.CustomerPortal):

    @http.route(["/product/categories"],
                type='json', auth='public')
    def ProductCategory(self, **kwargs):
        try:
            categories = request.env['product.template'].product_category()
            return categories or {
                'code':100,
                'error':'Failed to get product categories'
            }
        except Exception:
            logger.exception("Failed to get product categories")

        return request.not_found()
    

    @http.route(["/product/variants"],
                type='json', auth='public')
    def ProductVariants(self, **kwargs):
        try:
            categories = request.env['product.template'].product_attributes()
            return categories or {
                'code':100,
                'error':'Failed to get product categories'
            }
        except Exception:
            logger.exception("Failed to get product variants")

        return request.not_found()

    def add_line(self, product_id,sale_order ,set_qty=1 ):
        """This route is called when adding a product to cart (no options)."""

        product_custom_attribute_values = None
        no_variant_attribute_values = None

        sale_order._cart_update(
            product_id=product_id,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )

    @http.route(['/product/laravel/order'], type="json", auth="public", website=True, sitemap=False)
    def hot_order(self, order):
        logger.info(_("json order came from lara is: \n %s" %order))
        try:
            sale_order = request.website.lara_get_order(order)
            
            for line in order['lines']:
                self.add_line(int( line['product_id']),sale_order, int(line['qty']))
            
            sale_order.with_context(send_email=True).action_confirm()
            sale_order.payment_automation()
            
        except UserError as e:
            logger.exception(_("An error ocurred when sale order created: \n %s" %e.args[0]))
            return json.dumps({
                'hasError':True,
                'message':e.args[0]
            })
            
        logger.info(_("order added successfuly: \n %s" %sale_order.id))
        return json.dumps({
                'hasError':False,
                'message':"order added successfuly",
                'order_id':sale_order.id
            })

            
   