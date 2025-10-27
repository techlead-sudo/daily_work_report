{
    'name': 'Daily Work Report',
    'version': '17.0.1.0.0',
    'summary': 'Comprehensive Daily Work Report Management System',
    'description': """
        Daily Work Report Management System
        ===================================
        
        This module provides a comprehensive daily work report system with:
        * Employee daily work reports with task tracking
        * Support staff reporting
        * Multi-level approval workflow
        * Manager and employee relationship management
        * Job status tracking
        * Concerns management
        * Advanced reporting and dashboard views
        
        Features:
        ---------
        * Daily task reporting with time tracking
        * Project and task management integration
        * Approval workflow (Draft -> Submitted -> Approved)
        * Support for multiple reporting managers
        * Half-day and weekend handling
        * Concerns tracking and action management
        * Role-based access control
    """,
    'category': 'Human Resources',
    'author': 'Tiju\'s Academy',
    'website': 'https://www.tijusacademy.com',
    'depends': ['base', 'web', 'mail', 'hr'],
    'data': [
        # Security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        
        # Data
        'data/job_status_data.xml',
        'data/mail_activity_data.xml',
        
        # Views
        'views/job_status_views.xml',
        'views/employee_report_views.xml',
        'views/support_staff_views.xml',
        'views/additional_manager_views.xml',
        'views/concerns_views.xml',
        'views/menus.xml',
        
        # Wizards
        'wizard/report_reject_wizard_views.xml',
        'wizard/concern_action_wizard_views.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'daily_work_report/static/src/css/daily_report.css',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}