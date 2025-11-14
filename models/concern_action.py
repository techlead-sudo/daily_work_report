from odoo import fields, models


class ConcernAction(models.Model):
    _name = 'concern.action'
    _description = 'Concern Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Title', required=True, tracking=True)
    employee_report_id = fields.Many2one('employee.report', string='Related Report')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    concern_type = fields.Selection([
        ('student', 'Student Concern'),
        ('employee', 'Employee Concern'),
        ('other', 'Other Concern')
    ], string='Concern Type', required=True)
    
    description = fields.Html(string='Description', required=True)
    action_taken = fields.Html(string='Action Taken')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('canceled', 'Canceled')
    ], string='Status', default='draft', tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium')
    
    assigned_to = fields.Many2one('hr.employee', string='Assigned To')
    action_date = fields.Date(string='Action Date')
    resolved_date = fields.Date(string='Resolved Date')
    
    def action_start_progress(self):
        self.state = 'in_progress'
    
    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Date.today()
        })
    
    def action_cancel(self):
        self.state = 'canceled'