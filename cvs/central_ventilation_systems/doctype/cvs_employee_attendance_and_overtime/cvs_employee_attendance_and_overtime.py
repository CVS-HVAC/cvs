# -*- coding: utf-8 -*-
# Copyright (c) 2017, sanjay.kumar@herculesglobal.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CVSEmployeeAttendanceandOvertime(Document):


	def get_employees_detail(self):
		departments = self.departments
		for d in self.get('departments'):
			post_date = self.get('attendance_date');
			employees = frappe.db.sql("Select name, department, employee_name, eligible_for_overtime from tabEmployee where department  = %s", (d.department,), as_dict = 1)
			in_time = frappe.db.sql("Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'in_time';")
			out_time = frappe.db.sql("Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'out_time';")
			breaktime = frappe.db.sql("Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'break_time';")
			holiday = frappe.db.sql("Select name from tabHoliday where holiday_date	 = %s;",(post_date,), as_dict = 1)
			for employee in employees:
				attendance = self.append('attendances', {})
				attendance.employee = employee.name
				attendance.department = employee.department
				attendance.employee_name = employee.employee_name
				attendance.eligible_for_overtime = employee.eligible_for_overtime
				attendance.in_time = in_time[0][0]
				attendance.out_time = out_time[0][0]
				attendance.default_in = in_time[0][0]
				attendance.default_out = out_time[0][0]
				attendance.breaktime = breaktime[0][0]
				if holiday:
					attendance.holiday = 1
					if employee.eligible_for_overtime:
						attendance.special_ot = 8
					else:
						attendance.total_hours = 8
				else:
					attendance.holiday = 0
					attendance.total_hours = 8
				attendance.attendance_date = post_date
				attendance.latency = 0
