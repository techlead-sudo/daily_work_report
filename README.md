# Daily Work Report Module

## Overview

The Daily Work Report module is a comprehensive solution for tracking and managing daily work activities of employees and support staff. It provides a structured workflow for reporting, reviewing, and approving daily tasks with built-in approval mechanisms and concern management.

## Features

### Core Functionality
- **Employee Daily Reports**: Track daily tasks with time allocation and status
- **Support Staff Reports**: Specialized reporting for support staff with categorized work types
- **Multi-level Approval Workflow**: Draft → Submitted → Approved/Rejected
- **Concern Management**: Track and manage employee, student, and other concerns
- **Additional Manager Support**: Employees can report to multiple managers
- **Job Status Tracking**: Configurable status options for task progression

### Key Components

#### 1. Employee Reports
- Daily task logging with project, task, and activity details
- Time tracking in HH:MM format
- Status tracking (Completed, In Progress, Pending, etc.)
- Summary and concern sections
- Automatic work hour calculations
- Half-day and weekend handling

#### 2. Support Staff Reports
- Three work categories: Yesterday Pending, Today Work, Balance Work
- Time-based work logging
- Separate summaries for each work type
- Start/end time tracking

#### 3. Approval System
- Role-based permissions (User, Staff, HOD, Director, Admin, Super Admin)
- Manager-specific reporting
- Date-based approval restrictions
- Rejection with reason tracking

#### 4. Concern Management
- Student, Employee, and Other concern categories
- Action tracking with priority levels
- Assignment and resolution workflow
- Integration with daily reports

### User Roles and Permissions

1. **User**: Can create and view own reports
2. **Staff**: Can create support staff reports
3. **Staff Manager**: Can approve support staff reports
4. **HOD (Head of Department)**: Can approve reports for today and yesterday
5. **Director/VP**: Can approve all reports with full access
6. **Admin**: Full system access
7. **Super Admin**: Complete configuration access
8. **Concern Managers**: Can manage employee concerns

### Installation

1. Copy the module to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "Daily Work Report" module
4. Configure user groups and permissions as needed

### Configuration

#### Initial Setup
1. **Job Statuses**: Configure available task statuses (Completed, In Progress, etc.)
2. **User Groups**: Assign users to appropriate groups
3. **Additional Managers**: Set up additional reporting relationships if needed

#### Default Job Statuses
The module comes with pre-configured job statuses:
- Completed
- In Progress
- Pending
- Blocked
- Cancelled
- On Hold

### Usage

#### For Employees
1. Navigate to DWR → Daily Work Report
2. Create a new report for the current date
3. Add daily tasks with time allocation and status
4. Fill in any concerns if applicable
5. Submit for manager approval

#### For Support Staff
1. Navigate to DWR → Support Staff Report
2. Create a new support staff report
3. Fill in yesterday's pending work, today's work, and balance work
4. Submit for approval

#### For Managers
1. Review submitted reports in the appropriate menu
2. Approve or reject reports with reasons
3. Monitor team productivity and concerns

#### For Concern Managers
1. Navigate to DWR → Employee Concerns
2. Review and manage concern actions
3. Track resolution progress

### Technical Details

#### Models
- `employee.report`: Main employee daily reports
- `report`: Individual task lines within reports
- `support.staff`: Support staff reports
- `support.work.line`: Work lines for support staff
- `job.status`: Configurable task statuses
- `employee.additional.manager`: Additional reporting relationships
- `concern.action`: Concern management and actions

#### Security
- Record-level security rules based on employee relationships
- Group-based access control
- Manager hierarchy respect

#### Workflows
- Automatic status transitions
- Email notifications (via Odoo's mail system)
- Activity tracking and reminders

### Customization

The module is designed to be easily customizable:
- Add new job statuses
- Modify approval workflows
- Extend concern categories
- Add custom fields to reports

### Dependencies
- base
- web
- mail
- hr

### Version
- Compatible with Odoo 17.0
- Version: 1.0.0

### Support
For support and customization requests, contact Tiju's Academy.

### License
LGPL-3