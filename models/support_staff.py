from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SupportStaff(models.Model):
    _name = 'support.staff'
    _description = 'Support Staff Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # Constants
    WORK_LINE_MODEL = 'support.work.line'

    name = fields.Many2one('hr.employee', string="Employee", 
                          default=lambda self: self.env.user.employee_id, readonly=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                   default=lambda self: self.env.user.employee_id.department_id, 
                                   readonly=True)
    branch_id = fields.Many2one('res.partner', string="Branch", 
                               compute='_compute_branch_id', store=True)
    date = fields.Date(string='Date', default=fields.Date.today)

    @api.depends('name')
    def _compute_branch_id(self):
        for record in self:
            # Simplified branch computation - can be extended based on company structure
            if record.name and record.name.company_id:
                record.branch_id = record.name.company_id.partner_id.id
            else:
                record.branch_id = False
    
    # Time fields
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    total_work_hours = fields.Char(string='Total Work Hours', compute='_compute_total_work_hours')
    
    # Work lines
    yesterday_wrk_support_ids = fields.One2many(WORK_LINE_MODEL, 'support_staff_id',
                                               domain=[('work_type', '=', 'yesterday')],
                                               string='Yesterday Pending Work')
    today_wrk_support_ids = fields.One2many(WORK_LINE_MODEL, 'support_staff_id',
                                           domain=[('work_type', '=', 'today')],
                                           string='Today Work')
    balance_wrk_support_ids = fields.One2many(WORK_LINE_MODEL, 'support_staff_id',
                                             domain=[('work_type', '=', 'balance')],
                                             string='Balance Work')
    
    # Inverse methods for the one2many fields
    @api.onchange('yesterday_wrk_support_ids')
    def _onchange_yesterday_work(self):
        for line in self.yesterday_wrk_support_ids:
            if not line.work_type:
                line.work_type = 'yesterday'
    
    @api.onchange('today_wrk_support_ids')
    def _onchange_today_work(self):
        for line in self.today_wrk_support_ids:
            if not line.work_type:
                line.work_type = 'today'
    
    @api.onchange('balance_wrk_support_ids')
    def _onchange_balance_work(self):
        for line in self.balance_wrk_support_ids:
            if not line.work_type:
                line.work_type = 'balance'
    
    # Summaries
    summary1 = fields.Html(string="Yesterday Work Summary")
    summary2 = fields.Html(string="Today Work Summary")
    summary3 = fields.Html(string="Balance Work Summary")
    
    # Approval fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    prepared_by = fields.Many2one('hr.employee', string="Prepared By", 
                                 default=lambda self: self.env.user.employee_id)
    approved_by = fields.Many2one('hr.employee', string="Approved By")
    
    # Computed fields for permissions
    is_manager = fields.Boolean(string="Is Manager", compute="_compute_is_manager")
    is_director = fields.Boolean(string='Is Director', compute="_compute_is_manager")

    @api.depends('start_time', 'end_time')
    def _compute_total_work_hours(self):
        for record in self:
            if record.start_time and record.end_time:
                total_hours = record.end_time - record.start_time
                hours = int(total_hours)
                minutes = int((total_hours - hours) * 60)
                record.total_work_hours = f"{hours:02d}:{minutes:02d}"
            else:
                record.total_work_hours = "00:00"

    @api.depends('name')
    def _compute_is_manager(self):
        for record in self:
            record.is_manager = record.name.parent_id.user_id == self.env.user
            record.is_director = self.env.user.has_group('daily_work_report.group_directors')

    @api.constrains('name', 'date')
    def _check_unique_record_per_day(self):
        for record in self:
            domain = [
                ('name', '=', record.name.id),
                ('date', '=', record.date),
                ('id', '!=', record.id),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("You have already submitted a support staff report for this day."))

    def action_submit(self):
        self.write({
            'state': 'submitted',
            'prepared_by': self.env.user.employee_id.id,
        })
        # Notify manager (direct manager) about submission
        for rec in self:
            try:
                manager = rec.name.parent_id if rec.name and rec.name.parent_id else False
                if manager:
                    manager_email = manager.work_email or (manager.user_id.partner_id.email if manager.user_id else False)
                    if manager_email:
                        subject = _("Support Staff Report submitted by %s") % (rec.name.name if rec.name else '')
                        body = _("<p>Hello %s,</p><p>%s has submitted a support staff report for %s.</p>") % (
                            manager.name or '', rec.name.name if rec.name else '', rec.date or '')
                        mail = self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_to': manager_email,
                        })
                        mail.send()
            except Exception:
                pass

    def action_approve(self):
        if self.is_director or self.is_manager:
            self.write({
                'state': 'approved',
                'approved_by': self.env.user.employee_id.id,
            })
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Approved',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise ValidationError(_("You are not authorized to approve this report"))

    def message_post(self, **kwargs):
        """Override to notify employee when a manager posts a comment."""
        res = super(SupportStaff, self).message_post(**kwargs)

        message_type = kwargs.get('message_type', 'comment')
        if message_type != 'comment':
            return res

        for rec in self:
            try:
                user = self.env.user
                is_mgr = False
                if rec.name and rec.name.parent_id and rec.name.parent_id.user_id == user:
                    is_mgr = True
                if is_mgr and rec.name:
                    employee_email = rec.name.work_email or (rec.name.user_id.partner_id.email if rec.name.user_id else False)
                    if employee_email:
                        body = kwargs.get('body') or ''
                        subject = _("Message from manager regarding your Support Staff Report")
                        mail = self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_to': employee_email,
                        })
                        mail.send()
            except Exception:
                pass

        return res

    def action_rejection(self):
        if self.is_director or self.is_manager:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Reason for Rejection'),
                'res_model': 'report.reject.wizard',
                'target': 'new',
                'view_mode': 'form',
                'context': {'default_support_staff_id': self.id},
            }
        else:
            raise ValidationError(_("You are not authorized to reject this report"))