from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import re


class Report(models.Model):
    _name = 'report'
    _description = 'Daily Work Report Line'
    _order = 'sequence, id'

    employee_id = fields.Many2one('employee.report', string='Employee Report', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Main fields
    project_id = fields.Char(string='Project', required=True)
    task_id = fields.Char(string='Task')
    activity = fields.Char(string='Activity')
    time_taken = fields.Char(string='Time Taken (HH:MM)', required=True, 
                            help='Format: HH:MM (e.g., 02:30)')
    current_status = fields.Many2one('job.status', string='Current Status', required=True)
    
    # Fields for incomplete tasks
    to_work_on = fields.Char(string='To Work On')
    expected_close_date = fields.Date(string='Expected Close Date')
    remarks_if_any = fields.Char(string='Remarks')

    @api.constrains('time_taken')
    def _check_time_format(self):
        """Validate time format HH:MM"""
        for record in self:
            if record.time_taken and not re.match(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$', record.time_taken):
                raise ValidationError(_("Time must be in HH:MM format (e.g., 02:00, 13:30)."))

    @api.constrains('current_status', 'to_work_on', 'expected_close_date')
    def _check_incomplete_task_requirements(self):
        """Check that incomplete tasks have required fields"""
        for record in self:
            if record.current_status and record.current_status.name.strip().lower() != 'completed':
                if not record.to_work_on or not record.expected_close_date:
                    task_name = record.task_id or record.project_id or 'Unnamed Task'
                    raise ValidationError(
                        _("For task '%s': When status is not 'Completed', both 'To Work On' and 'Expected Close Date' are mandatory.") % task_name)

    def name_get(self):
        """Custom name_get to show meaningful names"""
        result = []
        for record in self:
            name = record.project_id or 'No Project'
            if record.task_id:
                name += f" - {record.task_id}"
            if record.activity:
                name += f" ({record.activity})"
            result.append((record.id, name))
        return result