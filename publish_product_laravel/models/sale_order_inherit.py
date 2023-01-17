from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo import api, fields, models
from itertools import groupby
import logging
import pytz


_logger = logging.getLogger(__name__)


class SaleOrderInerit(models.Model):
    _inherit = 'sale.order'

    lara_order_id=fields.Integer("lara ID", help="Sale order id on laravel server")

    @api.model
    def create_cash_statement(self, invoice_name, payaction):
        last_payment = self.env['account.payment'].sudo().browse(payaction['res_id'])
        last_journal = self.env['account.bank.statement'].sudo().search([
                                                                ('journal_id', '=', last_payment.journal_id.id)],
                                                                 order='id desc', limit=1)
        lastpaymentid = last_payment.id
        journal_id = last_payment.journal_id.id
        date = last_payment.date
        nn = last_payment.name
        partner_id = last_payment.partner_id.id
        amount = last_payment.amount
        currency_id = last_payment.currency_id.id

        starting_balance = 0.00

        if last_journal:
            starting_balance = last_journal.balance_end_real
        ending_balance = starting_balance + amount
        computed_balance = amount
        line_payment_ref = last_payment.ref
        statement = self.env['account.bank.statement'].sudo().create({
            'journal_id': journal_id,
            'date': date,
            # 'balance_start': starting_balance,
            'balance_end_real': ending_balance,
            # 'balance_end': computed_balance,
            'state': 'open',
            'line_ids': [
                (0, 0, {
                    'payment_id': lastpaymentid,
                    'payment_ref': invoice_name,
                    'partner_id': last_payment.partner_id.id,
                    'amount': amount,
                    'date': date
                })
            ]
        })
        line_date = date
        line_partner_id = partner_id
        line_amount = amount
        line_journal_id = journal_id
        line_statement_id = statement.id
        line_counterpart_account_id = statement.journal_id.profit_account_id.id

        statement.button_post()
        statement.action_bank_reconcile_bank_statements()
        annos = self.env['account.reconcile.model'].sudo().browse(1)
        annos._apply_rules(statement.line_ids)
        statement.button_validate_or_action()


    @api.model
    def payment_automation(self):
        for rec in self:
#             self._cr.autocommit(False)
            odoobot = rec.env['res.users'].sudo().browse(1)
            _logger.info("user is %s - %s"%(odoobot.env.user,odoobot.env.user.tz))
            tt = datetime.now(pytz.timezone(odoobot.env.user.tz)).strftime('%z')
            
            diff_hour = int(tt[1:3]) + int(tt[3:]) / 60
            seq_transaction = 0
            rec_date_order = datetime.strptime('01/08/2015', '%d/%m/%Y').date()
            
            rec_date_order = rec.date_order
            rec_date_order2 = rec_date_order + timedelta(hours=3)  # diff_hour
            rec_date_order_invoice = datetime(rec_date_order2.year, rec_date_order2.month, rec_date_order2.day)

            if rec.state == 'sale':
                try:
                    super(SaleOrderInerit, rec)._action_cancel()
                except:
                    super(SaleOrderInerit, rec).action_cancel()
                rec.action_draft()
                # rec._modify_corder()
                try:
                    rec.saletype = False
                except:
                    pass
                rec.action_confirm()
            
                rec.date_order = rec_date_order
                super(SaleOrderInerit, rec)._create_invoices(final=True)
                rec.invoice_ids.invoice_date = rec_date_order_invoice

                rec.invoice_ids.action_post()
                inv_name = None
                for ii in rec.invoice_ids:
                    inv_name = ii.name

                ctx = dict(
                    active_ids=rec.invoice_ids.ids,
                    active_orders=rec.ids,
                    active_model='account.move')

                register_payment_wizard = self.env['account.payment.register'].sudo().with_context(ctx).create(
                    {
                        'amount': rec.invoice_ids.amount_residual,
                        'currency_id': rec.invoice_ids.currency_id.id,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'payment_method_line_id': 1,
                        'payment_date': rec_date_order_invoice
                    })
                pay_action = register_payment_wizard.action_create_payments()

                ##############################################
                qry = f"""
                        update account_move aa
                        set date='{rec_date_order_invoice}'
                        where aa.ref='{inv_name}' or aa.name='{inv_name}'
                        """
                self._cr.execute(qry)
                qry = f"""
                        update account_move_line aa
                        set date=(select MM.date from account_move  MM where  MM.id=aa.move_id)
                        where aa.ref='{inv_name}' or aa.move_name='{inv_name}'
                        """
                self._cr.execute(qry)
                self.create_cash_statement(inv_name, pay_action)
                if seq_transaction % 10 == 0:
                    self._cr.commit()
                ###############################################

#         self._cr.commit()

