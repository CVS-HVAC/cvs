# -*- coding: utf-8 -*-
# Copyright (c) 2017, sanjay.kumar@herculesglobal.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CVSEmployeeAttendanceandOvertime(Document):

	def get_employees_detail(self):
		# Clear Child Table
		self.set('attendances', {})
		# Iterating Data Based On Departments
		post_date = self.get('attendance_date');
		in_time = frappe.db.sql("Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'in_time';")
		out_time = frappe.db.sql("Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'out_time';")
		breaktime = frappe.db.sql("Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'break_time';")
		holiday = frappe.db.sql("Select name from tabHoliday where holiday_date	 = %s;",(post_date,), as_dict = 1)
		for d in self.get('departments'):
			# employees = frappe.db.sql("Select name, department, employee_name, eligible_for_overtime from tabEmployee where department  = %s", (d.department,), as_dict = 1)
			employees = frappe.db.sql(""" Select emp.name, emp.department, 
										emp.employee_name, emp.eligible_for_overtime
										FROM tabEmployee as emp WHERE department  = %s AND
										NOT EXISTS (SELECT 1 from `tabLeave Application` as la
										WHERE la.employee = emp.name
										AND la.status = 'Approved'
										AND %s BETWEEN la.from_date 
										AND la.to_date);""", (d.department,post_date,), as_dict = 1)
			# leave = frappe.db.sql("Select employee from `tabLeave Allocation` where from_date = %s or to_date = %s;",(post_date,post_date,), as_dict = 1)
			# Parsing the Data To Child Table
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

	def on_submit(self):
		attendences = self.get('attendances')
		for attendence in attendences:
			if attendence.total_hours == 0:
				s = frappe.new_doc("Leave Application")
				s.from_date = attendence.attendance_date
				s.to_date = attendence.attendance_date
				s.employee = attendence.employee
				s.leave_type = "Privilege Leave"
				s.insert()
				s.save()					
				# s.submit()

				return s

		return True












