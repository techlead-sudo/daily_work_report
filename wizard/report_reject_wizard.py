from odoo import api, fields, models, _


class ReportRejectWizard(models.TransientModel):
    _name = 'report.reject.wizard'
    _description = 'Report Reject Wizard'

    employee_report_id = fields.Many2one('employee.report', string='Employee Report')
    support_staff_id = fields.Many2one('support.staff', string='Support Staff Report')
    reason = fields.Text(string='Reason for Rejection', required=True)

    def action_reject_report(self):
        """Reject the report with reason"""
        if self.employee_report_id:
            self.employee_report_id.write({
                'state': 'draft',
                'reject_reason': self.reason
            })
            # Post message to chatter
            self.employee_report_id.message_post(
                body=_("Report sent back to draft. Reason: %s") % self.reason,
                message_type='comment'
            )
        elif self.support_staff_id:
            self.support_staff_id.write({
                'state': 'rejected',
            })
            # Post message to chatter
            self.support_staff_id.message_post(
                body=_("Report rejected. Reason: %s") % self.reason,
                message_type='comment'
            )
        
        return {'type': 'ir.actions.act_window_close'}