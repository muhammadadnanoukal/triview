from odoo import api,SUPERUSER_ID

def test_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['tanmya.sale.stage'].create({ 'code': 'draft', 'name': 'Quotation','stageorder':-20,'issystem':True})
    env['tanmya.sale.stage'].create({ 'code': 'sent', 'name': 'Quotation Sent','stageorder':-10,'issystem':True})
    env['tanmya.sale.stage'].create({ 'code': 'sale','name': 'Sales Order','stageorder':1000,'issystem':True})
    env['tanmya.sale.stage'].create({ 'code': 'done', 'name': 'Locked','stageorder':1100,'issystem':True})
    env['tanmya.sale.stage'].create({ 'code': 'cancel', 'name': 'Cancelled','stageorder':1200,'issystem':True})
    cr.execute(""" DROP SEQUENCE IF EXISTS seq_tanmia_stage_users
    """)
    cr.execute(""" CREATE SEQUENCE seq_tanmia_stage_users INCREMENT 1 START 1
    """)
    cr.execute(""" ALTER TABLE IF EXISTS res_users_tanmya_sale_stage_rel
    ADD COLUMN seq integer DEFAULT nextval('seq_tanmia_stage_users'::regclass)
    """)


