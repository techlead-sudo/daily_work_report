from odoo import fields, models


class JobStatus(models.Model):
    _name = 'job.status'
    _description = 'Job Status'
    _order = 'sequence, id'

    name = fields.Char('Status Name', required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer('Color Index', default=0)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Status name must be unique!')
    ]