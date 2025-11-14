from odoo import fields, models


class SupportWorkLine(models.Model):
    _name = 'support.work.line'
    _description = 'Support Work Line'

    support_staff_id = fields.Many2one('support.staff', string='Support Staff', ondelete='cascade')
    work_type = fields.Selection([
        ('yesterday', 'Yesterday Work'),
        ('today', 'Today Work'),
        ('balance', 'Balance Work')
    ], string='Work Type', required=True)
    
    name = fields.Char(string='Work Description', required=True)
    time_taken = fields.Char(string='Time Taken (HH:MM)', required=True)
    current_status = fields.Many2one('job.status', string='Status', required=True)