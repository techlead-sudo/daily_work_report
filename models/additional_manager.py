from odoo import fields, models


class EmployeeAdditionalManager(models.Model):
    _name = 'employee.additional.manager'
    _description = 'Employee Additional Reporting Manager'
    _rec_name = 'manager_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    manager_id = fields.Many2one('hr.employee', string='Manager', required=True)
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_employee_manager', 'unique(employee_id, manager_id)', 
         'An employee cannot have the same additional manager twice!')
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.employee_id.name} -> {record.manager_id.name}"
            result.append((record.id, name))
        return result