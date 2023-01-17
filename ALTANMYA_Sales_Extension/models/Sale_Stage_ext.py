from odoo import api, fields, models, tools
from datetime import date, datetime,timedelta



class TanmyaSaleExt(models.Model):
    _inherit = 'sale.order'

    saletype =fields.Many2one('tanmya.sale.stage.type',string='Order type',compute='_calc_stage',
                                  inverse='_get_type',tracking=3,
                                  store=True)
    state = fields.Selection(selection=lambda self: self.get_stages(), string='Status',
                             readonly=True, copy=False, index=True, tracking=3, default='draft'
                             )
    showpending=fields.Boolean(string='pending status',compute='_show_pending_status',depends=['state'],store=False)
    userisadmin = fields.Boolean(compute='_check_admin',default=True)

    @api.depends('amount_total', 'currency_id')
    def _calc_stage(self):
        tot =0
        currid=0

        for rec in self:
            tot +=rec.amount_total
            currid=rec.currency_id.id

        ret_type= self.env['tanmya.sale.stage.type'].search([('currency','=',currid),
                                                       ('minrange','<=',tot),
                                                       ('maxrange','>=',tot)],limit=1)
        if not ret_type:
            ret_type = self.env['tanmya.sale.stage.type'].search([('currency','=',False),
                ('minrange', '<=', tot), ('maxrange', '>=', tot)], limit=1)
        self.saletype=ret_type

    def _check_admin(self):
        ret = False
        if self.state in ('draft', 'sent'):
            ret = True
        elif self.state in ('sale','done'):
            ret = False
        else:
            user0 = self.env['res.users'].browse(self.env.uid)
            ret = user0.has_group('tanmya_sales_extension.altanmya_sales_stage_type')
        self.userisadmin = ret


    def _get_type(self):
        ret=False
        if self.state in ('draft', 'sent'):
            pass
        else:
            user0 = self.env['res.users'].browse(self.env.uid)
            ret=user0.has_group('tanmya_sales_extension.altanmya_sales_stage_type')
            if ret:
              self._change_type()
            else:
              raise ValidationError("A hacking is attempted")


    def _change_type(self):
        self.env['tanmya.sale.order.pending'].search([('user', '=', self.env.uid)
                                                                   , ('saleorder', '=', self.id)]
                                                                  ).unlink()
        for act in self.activity_ids:
            if act.activity_type_id.id == 4 and act.res_id == self.id :
                act.action_feedback('Request is changed')
        self.state='sent'
        rec_id = self.env['ir.model'].sudo().search([('model', '=', 'sale.order')], limit=1)
        if self.user_id:
            self.env['mail.activity'].sudo().create({
                'activity_type_id': 4,
                'date_deadline': date.today(),
                'summary': 'Sale type stage has changed',
                'user_id': self.user_id.id,
                'res_model_id': rec_id.id,
                'res_id': self.id
            })
        self.process_stages()


    def get_stages(self):
        lst=[]
        recset=self.env['tanmya.sale.stage'].search([],order = 'stageorder')
        for stg in recset:
            lst.append((stg.code,stg.name))
        return lst


    def dynamic_selection(self):
        select = [
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale', 'Sales Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled'),
        ]
        # if self.date_order:
        #         print('hi2')
        #         select = [('draft', 'Quotation'), ('sent', 'Quotation Sent')]
        #         select.extend([('iy', 'iy new'), ('sale', 'Sales Order'), ('done', 'Locked'), ('cancel', 'Cancelled')])
        return select
    def action_confirm(self):
        if self.saletype:
            if self.state in ('draft','sent'):
                newlist = sorted(self.saletype.stages, key=lambda x: x.stageorder)
                self.state=newlist[0].code
                self.process_stages()
        else:
            super(TanmyaSaleExt,self).action_confirm()

    def _show_pending_status(self):
        ret=False
        if self.saletype:
            if self.state in self.saletype.get_stage_list():
               # print('ok')
               # print(self.env.uid)
               # print(self.state)
               # print(self.id)
               # print('ok0')
               if self.env['tanmya.sale.order.pending'].search_count([('user','=',self.env.uid)
                                                                   ,('state','=',self.state)
                                                                   ,('saleorder','=',self.id)
                                                                   ,('status','=','waiting')]):
                   ret=True
        #            print('okakak')
        # print('done')
        # print(ret)
        self.showpending= ret



    def action_approve(self):
      rec=  self.env['tanmya.sale.order.pending'].search([
          ('user', '=', self.env.uid)
          , ('state', '=', self.state)
          , ('saleorder', '=', self.id)
          , ('status', '=', 'waiting')
           ], limit=1)
      if rec:
          oldstate=self.state
          rec[0].update({'status': 'approve'})
          for act in self.activity_ids:
              if act.activity_type_id.id==4 and act.res_id==self.id and act.user_id.id==self.env.uid:
                  act.action_feedback('Request is approved')
          self.check_stage()
          current_stage=self.env['tanmya.sale.stage'].sudo().search([('code','=',self.state)],limit=1)
          if current_stage.approvetype=='sequence' and oldstate==self.state:
                rec_next=self.env['tanmya.sale.order.pending'].search([('state', '=', self.state)
                                                               , ('saleorder', '=', self.id)
                                                               , ('status', '=', 'queue')]
                                                                ,order = 'userorder'
                                                                 , limit=1)
                rec_next[0].update({'status': 'waiting'})
                rec_id = self.env['ir.model'].sudo().search([('model', '=', 'sale.order')], limit=1)
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'date_deadline': date.today(),
                    'summary': 'Request to approve',
                    'user_id': rec_next.user.id,
                    'res_model_id': rec_id.id,
                    'res_id': self.id
                })







    def action_decline(self):
        rec = self.env['tanmya.sale.order.pending'].search([
            ('user', '=', self.env.uid)
            , ('state', '=', self.state)
            , ('saleorder', '=', self.id)
            , ('status', '=', 'waiting')
        ], limit=1)
        if rec:
            rec[0].update({'status': 'decline'})
            self.state='cancel'
            super(TanmyaSaleExt, self).action_cancel()



    def check_stage(self):
        #lst_users=list(filter(lambda s:s.code==self.state,self.saletype.stages))
        count_approve=self.env['tanmya.sale.order.pending'].search_count([('state', '=', self.state)
                                                               , ('saleorder', '=', self.id)
                                                               , ('status', '=', 'approve')])
        current_stage = self.env['tanmya.sale.stage'].sudo().search([('code', '=', self.state)], limit=1)
        newlist = sorted(self.saletype.stages, key=lambda x: x.stageorder)


        if len(current_stage.stageusers)==count_approve:
              if current_stage.code == newlist[len(newlist) - 1].code:
                  super(TanmyaSaleExt, self).action_confirm()
              else:
                  for x in range(0, len(newlist) - 1):
                        if newlist[x].code==current_stage.code:
                            self.state=newlist[x+1].code
                            self.process_stages()
                            break



    def process_stages(self):
        current_stage = self.env['tanmya.sale.stage'].sudo().search([('code', '=', self.state)], limit=1)
        uorder = 0
        rec_id=self.env['ir.model'].sudo().search([('model','=','sale.order')], limit=1)
       # print(rec_id)
        qquery=" select seq,res_users_id  from res_users_tanmya_sale_stage_rel  where tanmya_sale_stage_id=" + str(current_stage.id) + " order by seq"
        self.env.cr.execute(qquery)
        stage_users=self.env.cr.fetchall()
      #  print(stage_users)
        for usrs in stage_users: # current_stage.stageusers:
                    if current_stage.approvetype=='parallel':
                        self.env['tanmya.sale.order.pending'].create({
                            'user': usrs[1],
                            'saleorder':self.id,
                            'state':self.state,
                            'userorder':0
                        })
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': 4,
                            'date_deadline': date.today() ,
                            'summary': 'Request to approve',
                            'user_id': usrs[1],
                            'res_model_id': rec_id.id,
                            'res_id': self.id
                        })
                    else:
                        uorder = uorder+1
                        if uorder==1:
                            self.env['tanmya.sale.order.pending'].create({
                                'user': usrs[1],
                                'saleorder':self.id,
                                'state':self.state,
                                'status': 'waiting',
                                'userorder' :uorder
                            })
                            self.env['mail.activity'].sudo().create({
                                'activity_type_id': 4,
                                'date_deadline': date.today() ,
                                'summary': 'Request to approve',
                                'user_id': usrs[1],
                                'res_model_id': rec_id.id,
                                'res_id': self.id
                            })
                        else:
                            self.env['tanmya.sale.order.pending'].create({
                                'user': usrs[1],
                                'saleorder':self.id,
                                'state':self.state,
                                'status':'queue',
                                'userorder': uorder
                            })





    @api.model
    def create(self, vals_list):
       res = super(TanmyaSaleExt, self).create(vals_list)
       return res

    def write(self,vals):

        res = super(TanmyaSaleExt, self).write( vals)
        return res

    # @api.onchange('saletype')
    # def do_stuff(self):
    #   pass
