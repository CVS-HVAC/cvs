# -*- coding: utf-8 -*-
# Copyright (c) 2017, sanjay.kumar@herculesglobal.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _, msgprint, throw
import math
class CVSEmployeeAttendanceandOvertime(Document):

	def autoname(self):
		attendance_date = self.attendance_date
		from datetime import datetime
		self.employee_date = datetime.strptime(attendance_date, '%Y-%m-%d').strftime('%d-%m-%Y')
		return True

	def conversionInHours(self, hrs):
		hours = math.floor( hrs/60 ) + hrs % 60 / 100;
		return hours

	def conversionInMinutes(self, mins):
		minutes = math.floor(float(mins)) * 60 + (float(mins) - (math.floor(float(mins)))) * 100
		return minutes

	def get_totaltime(self, in_time, out_time, default_in):

		actual_in = in_time
		data = {}
		inn = "01-01-2018 " + in_time;
		out = "01-01-2018 " + out_time;
		from datetime import datetime
		time_in = datetime.strptime(inn, '%d-%m-%Y %H:%M:%S')
		time_out = datetime.strptime(out, '%d-%m-%Y %H:%M:%S')
		import datetime
		intime =  datetime.datetime(time_in.year, time_in.month, time_in.day, time_in.hour,15*(time_in.minute // 15))
		in_time = intime.strftime('%H:%M:%S')
		outtime =  datetime.datetime(time_out.year, time_out.month, time_out.day, time_out.hour,15*(time_out.minute // 15))
		out_time = outtime.strftime('%H:%M:%S')
		from datetime import datetime
		FMT = '%H:%M:%S'
		diff = datetime.strptime(out_time, FMT) - datetime.strptime(in_time, FMT)
		hours, remainder = divmod(diff.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		total =  str(hours) +"."+ str(minutes)

		hours, remainder = divmod(default_in.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		default_in =  str(hours) +":"+ str(minutes) +":00"

		tdelta = datetime.strptime(in_time, FMT) - datetime.strptime(default_in, FMT)
		hours, remainder = divmod(tdelta.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		latency =  str(hours) +"."+ str(minutes)
		data.update({'latency':latency})
		data.update({'time_out':out_time})
		data.update({'total':total})
		return data

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
			employees = frappe.db.sql(""" Select  	emp.name, 
													emp.department, emp.employee_name, 
													emp.eligible_for_overtime, 
													dep.in_time, dep.out_time,
													dep.break_time, dep.paid_hrs
													FROM tabEmployee as emp 
													JOIN tabDepartment as dep
													WHERE emp.department  = %s AND
													dep.name  = %s AND
													NOT EXISTS (SELECT 1 from `tabLeave Application` as la
													WHERE la.employee = emp.name
													AND la.status = 'Approved'
													AND %s BETWEEN la.from_date 
													AND la.to_date) AND
													NOT EXISTS (Select 1 from `tabCVS Employee Attendance` as ea
													WHERE ea.employee = emp.name 
													AND ea.attendance_date = %s);""", (d.department,d.department,post_date,post_date,), as_dict = 1)

			# Parsing the Data To Child Table
			for employee in employees:
				attendance = self.append('attendances', {})
				attendance.employee = employee.name
				attendance.department = employee.department
				attendance.employee_name = employee.employee_name
				attendance.eligible_for_overtime = employee.eligible_for_overtime
				attendance.in_time = employee.in_time #in_time[0][0]
				attendance.out_time = employee.out_time #out_time[0][0]
				attendance.default_in = employee.in_time #in_time[0][0]
				attendance.default_out = employee.out_time #out_time[0][0]
				attendance.breaktime = employee.break_time #breaktime[0][0]
				attendance.paid_hours = employee.paid_hrs
				attendance.default_paid_hrs = employee.paid_hrs
				date_format = "%m-%d-%Y %H:%M:%S"
				from datetime import datetime
				inn = "1-01-2018 " + str(employee.in_time)
				out = "1-01-2018 " + str(employee.out_time)
				time1  = datetime.strptime(inn, date_format)
				time2  = datetime.strptime(out, date_format)
				diff = time2 - time1
				diff_btw_times = (diff.seconds) / 3600
				attendance.total_hours = diff_btw_times
				if holiday:
					attendance.holiday = 1
					if employee.eligible_for_overtime:
						attendance.special_ot = diff_btw_times
					else:
						attendance.total_hours = diff_btw_times
				else:
					attendance.holiday = 0
					attendance.total_hours = diff_btw_times
				attendance.attendance_date = post_date
				attendance.latency = 0

	def validate(self):
		self.set_missing_values();

	def set_missing_values(self, for_validate=False):
		post_date = self.get('attendance_date');
		if self.attendances:
			for attendance in self.attendances:
				if len(attendance.out_time) == 1:
					attendance.paid_hours = 0
					attendance.normal_ot = 0
					attendance.special_ot = 0
				else:
					exist = frappe.db.sql(""" Select 1 from `tabCVS Employee Attendance` 
												where employee = %s
												and attendance_date = %s""", (attendance.employee,self.attendance_date,), as_dict=1)
					if exist:
						frappe.throw(_("Employee "+attendance.employee+" Already Created For The Attendance Date."))

					holiday = frappe.db.sql("Select name from tabHoliday where holiday_date	 = %s;",(self.attendance_date,), as_dict = 1)
					res = frappe.db.sql("""
										Select  e.department, e.employee_name, 
										e.eligible_for_overtime, d.in_time, d.out_time,
										d.break_time, d.paid_hrs from tabDepartment d 
										join tabEmployee e on (e.department = d.name) 
										where e.name = %s
										""", (attendance.employee), as_dict=1)

					if not res:
						throw(_('Invalid Employee Data'))
						return {}
					else:
						res = res[0]
					if not attendance.attendance_date:
						attendance.attendance_date = post_date
					if not attendance.breaktime:
						attendance.breaktime = res['break_time']
					if not attendance.eligible_for_overtime:
						attendance.eligible_for_overtime = res['eligible_for_overtime']
					if not attendance.employee_name:
						attendance.employee_name = res['employee_name']
					if not attendance.department:
						attendance.department = res['department']
					if not attendance.default_paid_hrs:
						attendance.default_paid_hrs = res['paid_hrs']
					if not attendance.total_hours:
						tot = self.get_totaltime(attendance.in_time,attendance.out_time,res['in_time'])
						attendance.total_hours = tot['total']
						attendance.latency = tot['latency']
						if not attendance.paid_hours:
							# attendance.paid_hours = res['paid_hrs']
							total = self.conversionInMinutes(tot['total']) - self.conversionInMinutes(res['break_time'])
							totalhrs = self.conversionInHours(total)

							if float(totalhrs) > float(res['paid_hrs']):
								attendance.paid_hours = res['paid_hrs']
							else:
								attendance.paid_hours = totalhrs
						extra = self.conversionInMinutes(tot['total']) - self.conversionInMinutes(res['paid_hrs']) - self.conversionInMinutes(res['break_time'])
						extra_hrs = self.conversionInHours(extra)
						holiday = frappe.db.sql("Select name from tabHoliday where holiday_date	 = %s;",(self.attendance_date,), as_dict = 1)
						if float(extra_hrs) > 0:
							if res['eligible_for_overtime'] == 1:
								if holiday:
									attendance.holiday = 1
									attendance.special_ot = extra_hrs
								else:	
									attendance.normal_ot = extra_hrs
					if not attendance.holiday:
						if res['eligible_for_overtime'] == 1:
							if holiday:
								tot = self.get_totaltime(attendance.in_time,attendance.out_time,res['in_time'])
								# extra = self.conversionInMinutes(tot['total']) - self.conversionInMinutes(res['paid_hrs']) - self.conversionInMinutes(res['break_time'])
								# extra_hrs = self.conversionInHours(extra)
								attendance.holiday = 1
								attendance.special_ot = tot['total']
								attendance.normal_ot = 0
	def on_submit(self):
		attendences = self.get('attendances')
		departments = self.get('departments')
		leave = frappe.db.sql("""Select value from tabSingles where doctype = 'CVS Employee Attendance Settings' and field = 'leave';""")
		if departments:
			if attendences:
				for attendence in attendences:
					if attendence.total_hours == 0:
						s = frappe.new_doc("Leave Application")
						s.from_date = attendence.attendance_date
						s.to_date = attendence.attendance_date
						s.employee = attendence.employee
						s.leave_type = leave[0][0]
						s.insert()
						s.save()					
						# s.submit()

						return s
			else:
				frappe.throw(_("Please Choose The Employee"))

		else:
			frappe.throw(_("Please Choose The Department"))

		return True

@frappe.whitelist()
def get_emp_depart(employee, depart = None):
	res = frappe.db.sql("""
		Select  e.department, e.employee_name, 
				e.eligible_for_overtime, d.in_time, d.out_time,
				d.break_time, d.paid_hrs from tabDepartment d 
				join tabEmployee e on (e.department = d.name) 
				where e.name = %s
	""", (employee), as_dict=1)

	if not res:
		return {}

	res = res[0]
	return res

@frappe.whitelist()
def get_intime(intime, default_in):
	actual_in = intime
	data = {}
	inn = "01-01-2018 " + intime;
	from datetime import datetime
	time_in = datetime.strptime(inn, '%d-%m-%Y %H:%M:%S')
	import datetime
	intime =  datetime.datetime(time_in.year, time_in.month, time_in.day, time_in.hour,15*(time_in.minute // 15))
	in_time = intime.strftime('%H:%M:%S')
	from datetime import datetime
	FMT = '%H:%M:%S'
	tdelta = datetime.strptime(actual_in, FMT) - datetime.strptime(default_in, FMT)
	hours, remainder = divmod(tdelta.seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	latency =  str(hours) +"."+ str(minutes)
	data.update({'time_in':actual_in})
	data.update({'latency':latency})
	return data

@frappe.whitelist()
def get_outtime(intime, outtime):
	actual_out = outtime
	data = {}
	inn = "01-01-2018 " + intime;
	out = "01-01-2018 " + outtime;
	from datetime import datetime
	time_in = datetime.strptime(inn, '%d-%m-%Y %H:%M:%S')
	time_out = datetime.strptime(out, '%d-%m-%Y %H:%M:%S')
	import datetime
	intime =  datetime.datetime(time_in.year, time_in.month, time_in.day, time_in.hour,15*(time_in.minute // 15))
	in_time = intime.strftime('%H:%M:%S')
	outtime =  datetime.datetime(time_out.year, time_out.month, time_out.day, time_out.hour,15*(time_out.minute // 15))
	out_time = outtime.strftime('%H:%M:%S')
	from datetime import datetime
	FMT = '%H:%M:%S'
	diff = datetime.strptime(out_time, FMT) - datetime.strptime(in_time, FMT)
	hours, remainder = divmod(diff.seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	total =  str(hours) +"."+ str(minutes)
	data.update({'time_out':actual_out})
	data.update({'total':total})
	return data