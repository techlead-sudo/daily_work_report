from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class DWREscalation(models.Model):
    _name = 'dwr.escalation'
    _description = 'DWR Escalation Queue'

    employee_report_id = fields.Many2one('employee.report', string='Employee Report', required=True, ondelete='cascade')
    scheduled_datetime = fields.Datetime(string='Scheduled Datetime', required=True)
    processed = fields.Boolean(string='Processed', default=False)
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Created On', default=fields.Datetime.now)

    @api.model
    def process_due_escalations(self):
        """Process escalations: escalate up hierarchy every 15 hours until top manager is reached."""
        import pytz
        now = fields.Datetime.now()
        esc_recs = self.search([('processed', '=', False), ('scheduled_datetime', '<=', now)])
        _logger.info('DWR Escalation: processing %s records', len(esc_recs))
        for esc in esc_recs:
            try:
                report = esc.employee_report_id
                if not report:
                    esc.processed = True
                    continue
                if report.state != 'submitted':
                    _logger.info('Report %s state is %s, skipping escalation', report.id, report.state)
                    esc.processed = True
                    continue
                # Find current escalation manager (from last escalation)
                last_manager = None
                if esc.created_by and esc.created_by.employee_id:
                    last_manager = esc.created_by.employee_id
                else:
                    last_manager = report.reporting_manager_id or (report.name.parent_id if report.name else False)
                # Escalate to next manager up
                next_manager = last_manager.parent_id if last_manager else None
                if not next_manager:
                    _logger.warning('No higher manager to escalate to for report %s; marking processed', report.id)
                    esc.processed = True
                    continue
                next_manager_email = next_manager.work_email or (next_manager.user_id.partner_id.email if next_manager.user_id else False)
                if not next_manager_email:
                    _logger.warning('Escalation target %s has no email; marking processed', next_manager.id)
                    esc.processed = True
                    continue
                # Send escalation email
                email_from = self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                if not email_from:
                    email_from = self.env.company.email or (self.env.user.company_id.email if self.env.user.company_id else False)
                if not email_from:
                    catchall = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')
                    if catchall:
                        email_from = 'no-reply@' + catchall
                    else:
                        email_from = 'no-reply@example.com'
                subject = _('Escalation: Daily Work Report requires your approval')
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                record_url = f"{base_url}/web#id={report.id}&model={report._name}&view_type=form"
                body = _(
                    '<p>Hello %(manager)s,</p>'
                    '<p>%(employee)s has a pending daily work report submitted on %(date)s that requires your review and approval.</p>'
                    '<p>This request was escalated because the previous manager did not act within 15 hours. If you do not approve within 15 hours, it will escalate to your manager.</p>'
                    '<p><a href="%(url)s" style="background-color: #875A7B; padding: 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;">View Report</a></p>'
                    '<p>Thank you.</p>'
                ) % {
                    'manager': next_manager.name,
                    'employee': report.name.name if report.name else '',
                    'date': report.date or '',
                    'url': record_url
                }
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': next_manager_email,
                    'email_from': email_from,
                    'auto_delete': False,
                    'state': 'outgoing',
                    'message_type': 'email',
                    'model': report._name,
                    'res_id': report.id,
                }
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.sudo().send(raise_exception=False)
                report.message_post(
                    body=_('Escalation notification sent to %s. If not approved within 15 hours, it will escalate to the next manager.') % (next_manager.name,),
                    message_type='notification'
                )
                _logger.info('Escalation: sent mail.mail %s for report %s', mail.id, report.id)
                esc.processed = True
                # Schedule next escalation at next day's 14:00 IST if still not approved
                if next_manager.parent_id:
                    ist = pytz.timezone('Asia/Kolkata')
                    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                    now_ist = now_utc.astimezone(ist)
                    next_day = now_ist.date() + timedelta(days=1)
                    target_time = datetime(next_day.year, next_day.month, next_day.day, 14, 0, 0)
                    scheduled_ist = ist.localize(target_time)
                    scheduled_utc = scheduled_ist.astimezone(pytz.utc)
                    self.env['dwr.escalation'].sudo().create({
                        'employee_report_id': report.id,
                        'scheduled_datetime': fields.Datetime.to_string(scheduled_utc),
                        'created_by': next_manager.user_id.id if next_manager.user_id else None,
                    })
            except Exception as e:
                _logger.error('Error processing escalation %s: %s', esc.id, e, exc_info=True)
                # Do not mark processed to allow retry next run
        return True