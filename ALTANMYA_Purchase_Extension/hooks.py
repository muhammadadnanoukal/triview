from odoo import api,SUPERUSER_ID

def test_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['tanmya.purchase.stage'].create({ 'code': 'draft', 'name': 'RFQ','stageorder':-20,'issystem':True})
    env['tanmya.purchase.stage'].create({ 'code': 'sent', 'name': 'Sent Sent','stageorder':-10,'issystem':True})
    env['tanmya.purchase.stage'].create({ 'code': 'to approve','name': 'To Approve','stageorder':-5,'issystem':True})
    env['tanmya.purchase.stage'].create({ 'code': 'purchase','name': 'Purchase Order','stageorder':1000,'issystem':True})
    env['tanmya.purchase.stage'].create({ 'code': 'done', 'name': 'Locked','stageorder':1100,'issystem':True})
    env['tanmya.purchase.stage'].create({ 'code': 'cancel', 'name': 'Cancelled','stageorder':1200,'issystem':True})


    cr.execute(""" DROP SEQUENCE IF EXISTS seq_tanmia_pstage_users
    """)
    cr.execute(""" CREATE SEQUENCE seq_tanmia_pstage_users INCREMENT 1 START 1
    """)
    cr.execute(""" ALTER TABLE IF EXISTS res_users_tanmya_purchase_stage_rel
    ADD COLUMN seq integer DEFAULT nextval('seq_tanmia_pstage_users'::regclass)
    """)


