import re
import calendar
from datetime import date, datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class EmployeeReport(models.Model):
    _name = 'employee.report'
    _description = 'Employee Daily Work Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Many2one('hr.employee', string="Employee", 
                          default=lambda self: self.env.user.employee_id, readonly=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                   default=lambda self: self.env.user.employee_id.department_id, 
                                   readonly=True)
    branch_id = fields.Many2one('res.partner', string="Branch", 
                               compute='_compute_branch_id', store=True)
    reporting_manager_id = fields.Many2one('hr.employee', string="Reporting Manager", 
                                          help="Select the specific manager this report is intended for")

    @api.depends('name')
    def _compute_branch_id(self):
        for record in self:
            # Simplified branch computation - can be extended based on company structure
            if record.name and record.name.company_id:
                record.branch_id = record.name.company_id.partner_id.id
            else:
                record.branch_id = False

    # Work report lines
    report_ids = fields.One2many('report', 'employee_id', string="Daily Report", 
                                default=lambda self: self._default_report_ids())

    # Time calculations
    total_work_hours = fields.Char(string='Total Work Hours', compute='_compute_total_work_hours', store=True)
    actual_work_hours = fields.Char(string='Actual Work Hours', compute='_compute_actual_work_hours', store=True)
    total_work_minutes = fields.Integer(string='Total Work Minutes', compute='_compute_actual_work_hours', store=True)

    # Dates and workflow
    date = fields.Date(string='Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)

    # Approval tracking
    prepared_by = fields.Many2one('hr.employee', string="Prepared By", 
                                 default=lambda self: self.env.user.employee_id)
    approved_by = fields.Many2one('hr.employee', string="Approved By")
    submitted_time = fields.Datetime(string='Submission On', readonly=True, tracking=True)
    approved_time = fields.Datetime(string='Approved On', readonly=True, tracking=True)

    # Summary and concerns
    summary = fields.Html(string="Summary")
    student_concerns = fields.Text(string="Student Concerns")
    employee_concerns = fields.Text(string="Employee Concerns")
    other_concerns = fields.Text(string="Other Concerns")
    has_concerns = fields.Boolean(string="Has Concerns")
    reject_reason = fields.Text(string='Rejection Reason', tracking=True)

    # Computed fields for permissions and logic
    is_manager = fields.Boolean(string="Is Manager", compute="_compute_is_manager")
    is_director = fields.Boolean(string='Is Director', compute="_compute_is_manager")
    is_hod = fields.Boolean(string='Is HOD', compute="_compute_is_manager")
    is_half_day = fields.Boolean(string="Half day report", compute="_compute_is_half_day")
    available_manager_ids = fields.Many2many('hr.employee', compute='_compute_available_manager_ids')

    def _default_report_ids(self):
        """Create default report line for refreshment break"""
        today = date.today()
        
        # Check if today is 1st or 3rd Saturday (half day)
        if today.weekday() == calendar.SATURDAY:
            month_calendar = calendar.Calendar()
            saturdays = [
                day for day in month_calendar.itermonthdays2(today.year, today.month)
                if day[0] != 0 and day[1] == calendar.SATURDAY
            ]
            if (today.day == saturdays[0][0] or (len(saturdays) > 2 and today.day == saturdays[2][0])):
                return []

        # Default refreshment break entry
        completed_status = self.env['job.status'].search([('name', '=', 'Completed')], limit=1)
        return [(0, 0, {
            'project_id': 'Refreshment',
            'task_id': 'Break',
            'activity': 'Tea/Coffee Break',
            'time_taken': '00:30',
            'current_status': completed_status.id if completed_status else False
        })]

    @api.depends('date', 'is_half_day')
    def _compute_total_work_hours(self):
        """Compute total work hours based on working schedule and half-day conditions"""
        for record in self:
            hours_per_day = 8.0  # Default working hours
            
            # Apply half-day if applicable
            if record.is_half_day:
                hours_per_day = 4.0

            # Convert to HH:MM format
            hours = int(hours_per_day)
            minutes = int((hours_per_day - hours) * 60)
            record.total_work_hours = f"{hours:02d}:{minutes:02d}"

    @api.depends('report_ids.time_taken')
    def _compute_actual_work_hours(self):
        """Compute actual work hours from report lines"""
        for record in self:
            total_minutes = 0
            for report in record.report_ids:
                if report.time_taken and isinstance(report.time_taken, str):
                    try:
                        hours, minutes = map(int, report.time_taken.split(':'))
                        total_minutes += hours * 60 + minutes
                    except (ValueError, AttributeError):
                        continue

            record.total_work_minutes = total_minutes
            hours, minutes = divmod(total_minutes, 60)
            record.actual_work_hours = f"{hours:02d}:{minutes:02d}"

    @api.depends('date')
    def _compute_is_half_day(self):
        """Check if today is a half-day (1st or 3rd Saturday)"""
        for record in self:
            record.is_half_day = False
            check_date = record.date or fields.Date.today()
            
            # Check if the date is 1st or 3rd Saturday (half day)
            if check_date.weekday() == calendar.SATURDAY:
                month_calendar = calendar.Calendar()
                saturdays = [
                    day for day in month_calendar.itermonthdays2(check_date.year, check_date.month)
                    if day[0] != 0 and day[1] == calendar.SATURDAY
                ]
                if check_date.day == saturdays[0][0] or (len(saturdays) > 2 and check_date.day == saturdays[2][0]):
                    record.is_half_day = True

    @api.depends('name')
    def _compute_available_manager_ids(self):
        """Compute available managers for employee"""
        for record in self:
            available_managers = []
            if record.name:
                # Add direct manager
                if record.name.parent_id:
                    available_managers.append(record.name.parent_id.id)
                
                # Add additional managers
                add_managers = self.env['employee.additional.manager'].search([
                    ('employee_id', '=', record.name.id),
                    ('active', '=', True)
                ])
                for add_manager in add_managers:
                    available_managers.append(add_manager.manager_id.id)
            
            record.available_manager_ids = available_managers
            
            # Auto-select manager if only one available
            if len(available_managers) == 1 and not record.reporting_manager_id and record.state == 'draft':
                record.reporting_manager_id = available_managers[0]

    @api.depends('name', 'reporting_manager_id')
    def _compute_is_manager(self):
        """Compute user permissions"""
        for record in self:
            # Check if user is direct manager
            is_direct_manager = record.name.parent_id.user_id == self.env.user
            
            # Check if user is the specific reporting manager
            is_reporting_manager = False
            if record.reporting_manager_id and record.reporting_manager_id.user_id == self.env.user:
                is_reporting_manager = True
                
            # Check if user is an additional manager
            is_additional_manager = False
            if record.name:
                additional_manager_recs = self.env['employee.additional.manager'].search([
                    ('employee_id', '=', record.name.id),
                    ('manager_id.user_id', '=', self.env.user.id)
                ])
                is_additional_manager = bool(additional_manager_recs)
            
            record.is_manager = is_direct_manager or is_reporting_manager or is_additional_manager
            record.is_director = self.env.user.has_group('daily_work_report.group_directors')
            record.is_hod = self.env.user.has_group('daily_work_report.group_hod')

    @api.constrains('name', 'date', 'reporting_manager_id')
    def _check_unique_record_per_day(self):
        """Ensure one report per employee per day per manager"""
        for record in self:
            domain = [
                ('name', '=', record.name.id),
                ('date', '=', record.date),
                ('id', '!=', record.id),
            ]
            
            if record.reporting_manager_id:
                domain.append(('reporting_manager_id', '=', record.reporting_manager_id.id))
            else:
                domain.append(('reporting_manager_id', '=', False))
                
            if self.search_count(domain) > 0:
                if record.reporting_manager_id:
                    raise ValidationError(_("You have already submitted a report for this day to manager %s.") % record.reporting_manager_id.name)
                else:
                    raise ValidationError(_("You have already submitted a report for this day."))

    def action_submit(self):
        """Submit the report for approval"""
        today = fields.Date.today()
        yesterday = fields.Date.today() - timedelta(days=1)
        
        # Validate date restrictions
        if not self.is_director:
            if self.is_hod:
                if self.date not in [today, yesterday]:
                    raise ValidationError(_("As HOD, you can only submit reports for today and yesterday"))
            elif self.date != today:
                raise ValidationError(_("You can only submit reports for today"))
        
        # Validate incomplete tasks
        for report in self.report_ids:
            if report.current_status.name.strip().lower() != 'completed':
                if not report.to_work_on or not report.expected_close_date:
                    raise ValidationError(
                        _("For task '%s': When status is not 'Completed', both 'To Work On' and 'Expected Close Date' are mandatory.") % report.task_id)
        
        # Check for concerns
        if self.student_concerns or self.employee_concerns or self.other_concerns:
            self.has_concerns = True
        
        self.write({
            'state': 'submitted',
            'prepared_by': self.env.user.employee_id.id,
            'submitted_time': fields.Datetime.now()
        })

    def action_approve(self):
        """Approve the report"""
        today = fields.Date.today()
        
        if self.is_director:
            self.write({
                'state': 'approved',
                'approved_by': self.env.user.employee_id.id,
                'approved_time': fields.Datetime.now()
            })
            self.activity_ids.unlink()
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Approved',
                    'type': 'rainbow_man',
                }
            }
        elif self.is_manager:
            yesterday = fields.Date.today() - timedelta(days=1)
            
            # Date validation for managers
            if self.is_hod:
                if self.date not in [today, yesterday]:
                    raise UserError(_("As HOD, you can only approve reports for today and yesterday"))
            elif self.date != today:
                raise UserError(_("You can only approve today's reports"))
                
            self.write({
                'state': 'approved',
                'approved_by': self.env.user.employee_id.id,
                'approved_time': fields.Datetime.now()
            })
            self.activity_ids.unlink()
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Approved',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise ValidationError(_("You are not authorized to approve this report"))

    def action_reject(self):
        """Reject the report with reason"""
        today = fields.Date.today()
        
        if self.is_director:
            return self._open_reject_wizard()
        elif self.is_manager:
            yesterday = fields.Date.today() - timedelta(days=1)
            
            # Date validation for managers
            if self.is_hod:
                if self.date not in [today, yesterday]:
                    raise UserError(_("As HOD, you can only reject reports for today and yesterday"))
            elif self.date != today:
                raise UserError(_("You can only reject today's reports"))
            
            return self._open_reject_wizard()
        else:
            raise ValidationError(_("You are not authorized to reject this report"))

    def _open_reject_wizard(self):
        """Open reject wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Report'),
            'res_model': 'report.reject.wizard',
            'target': 'new',
            'view_mode': 'form',
            'context': {'default_employee_report_id': self.id},
        }

    def action_quick_create_concern(self):
        """Quick create concern action"""
        self.ensure_one()
        
        default_title = _("Action against {}'s concern on {}").format(
            self.name.name,
            self.date.strftime('%d-%m-%Y') if self.date else ''
        )

        return {
            'name': _('Create Concern Action'),
            'type': 'ir.actions.act_window',
            'res_model': 'concern.action.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_report_id': self.id,
                'default_name': default_title,
            },
        }