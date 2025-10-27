from odoo import api, fields, models, _


class ConcernActionWizard(models.TransientModel):
    _name = 'concern.action.wizard'
    _description = 'Concern Action Creation Wizard'

    employee_report_id = fields.Many2one('employee.report', string='Employee Report', required=True)
    name = fields.Char(string='Action Title', required=True)
    concern_type = fields.Selection([
        ('student', 'Student Concern'),
        ('employee', 'Employee Concern'),
        ('other', 'Other Concern')
    ], string='Concern Type', required=True)
    description = fields.Html(string='Description', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium')
    assigned_to = fields.Many2one('hr.employee', string='Assigned To')

    @api.onchange('concern_type')
    def _onchange_concern_type(self):
        """Auto-fill description based on concern type and employee report"""
        if self.employee_report_id and self.concern_type:
            concern_text = ""
            if self.concern_type == 'student' and self.employee_report_id.student_concerns:
                concern_text = self.employee_report_id.student_concerns
            elif self.concern_type == 'employee' and self.employee_report_id.employee_concerns:
                concern_text = self.employee_report_id.employee_concerns
            elif self.concern_type == 'other' and self.employee_report_id.other_concerns:
                concern_text = self.employee_report_id.other_concerns
            
            if concern_text:
                self.description = f"<p><strong>Original Concern:</strong></p><p>{concern_text}</p><br/><p><strong>Action Required:</strong></p><p></p>"

    def action_create_concern_action(self):
        """Create concern action record"""
        vals = {
            'name': self.name,
            'employee_report_id': self.employee_report_id.id,
            'employee_id': self.employee_report_id.name.id,
            'concern_type': self.concern_type,
            'description': self.description,
            'priority': self.priority,
            'assigned_to': self.assigned_to.id if self.assigned_to else False,
            'action_date': fields.Date.today(),
        }
        
        concern_action = self.env['concern.action'].create(vals)
        
        # Mark the employee report as having concerns processed
        self.employee_report_id.has_concerns = True
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Concern Action'),
            'res_model': 'concern.action',
            'res_id': concern_action.id,
            'view_mode': 'form',
            'target': 'current',
        }