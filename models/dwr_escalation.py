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
        """Called by cron: process escalations whose scheduled_datetime <= now and not processed."""
        now = fields.Datetime.now()
        esc_recs = self.search([('processed', '=', False), ('scheduled_datetime', '<=', now)])
        _logger.info('DWR Escalation: processing %s records', len(esc_recs))
        for esc in esc_recs:
            try:
                report = esc.employee_report_id
                if not report:
                    esc.processed = True
                    continue
                # Only escalate if still submitted
                if report.state != 'submitted':
                    _logger.info('Report %s state is %s, skipping escalation', report.id, report.state)
                    esc.processed = True
                    continue
                # Determine reporting manager (original)
                reporting_manager = report.reporting_manager_id or (report.name.parent_id if report.name else False)
                if not reporting_manager:
                    _logger.warning('Report %s has no reporting manager; marking escalation processed', report.id)
                    esc.processed = True
                    continue
                # Manager's manager
                mgr_mgr = reporting_manager.parent_id
                if not mgr_mgr:
                    _logger.warning('Reporting manager for report %s has no manager to escalate to', report.id)
                    esc.processed = True
                    continue
                # Get email
                mgr_mgr_email = mgr_mgr.work_email or (mgr_mgr.user_id.partner_id.email if mgr_mgr.user_id else False)
                if not mgr_mgr_email:
                    _logger.warning('Escalation target %s has no email; marking processed', mgr_mgr.id)
                    esc.processed = True
                    continue
                # Use submission template if available
                try:
                    template = self.env.ref('daily_work_report.mail_template_dwr_submission')
                except Exception:
                    template = False
                # Determine sender
                email_from = self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                if not email_from:
                    email_from = self.env.company.email or (self.env.user.company_id.email if self.env.user.company_id else False)
                if not email_from:
                    catchall = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')
                    if catchall:
                        email_from = 'no-reply@' + catchall
                    else:
                        email_from = 'no-reply@example.com'
                if template:
                    template.sudo().send_mail(report.id, force_send=True, email_values={'email_from': email_from, 'email_to': mgr_mgr_email})
                    report.message_post(body=_('Escalation: submission notification sent to %s') % (mgr_mgr.name,), message_type='notification')
                    _logger.info('Escalation: sent notification for report %s to %s', report.id, mgr_mgr_email)
                else:
                    # Fallback: create mail.mail
                    subject = _('Escalated Daily Work Report submitted by %s') % (report.name.name if report.name else '')
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    record_url = f"{base_url}/web#id={report.id}&model={report._name}&view_type=form"
                    body = _('<p>Hello %s,</p><p>%s has a pending daily work report submitted on %s which required review. You are receiving this because the reporting manager was unavailable.</p><p>View: %s</p>') % (mgr_mgr.name, report.name.name if report.name else '', report.date or '', record_url)
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': mgr_mgr_email,
                        'email_from': email_from,
                        'auto_delete': False,
                        'state': 'outgoing',
                        'message_type': 'email',
                        'model': report._name,
                        'res_id': report.id,
                    }
                    mail = self.env['mail.mail'].sudo().create(mail_values)
                    mail.sudo().send(raise_exception=False)
                    report.message_post(body=_('Escalation: submission notification sent to %s') % (mgr_mgr.name,), message_type='notification')
                    _logger.info('Escalation fallback: sent mail.mail %s for report %s', mail.id, report.id)
                esc.processed = True
            except Exception as e:
                _logger.error('Error processing escalation %s: %s', esc.id, e, exc_info=True)
                # Do not mark processed to allow retry next run
        return True