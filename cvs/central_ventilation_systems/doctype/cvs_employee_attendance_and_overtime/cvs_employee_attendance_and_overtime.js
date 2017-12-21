// Copyright (c) 2017, sanjay.kumar@herculesglobal.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CVS Employee Attendance and Overtime', {

	setup: function(frm) {
		frm.get_docfield("attendances").allow_bulk_edit = 1;
		frm.set_df_property("attendance_date", "read_only", frm.doc.__islocal ? 0 : 1);
		// frm.setup_queries();
	},


	onload: function(frm) {
		frm.set_query("department", "departments", function() {
				 return{
					filters:{ 
								'is_attendance_required' : ["=", 1]
							}
						}
			
		});

		frm.set_query("employee", "attendances", function() {
				 return{
					filters:{ 
								'department' : ["!=", "Management"]
							}
						}
			
		});
	},

	attendance_date: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.attendances){
			for (var i =0; i < cur_frm.doc.attendances.length; i++){
				cur_frm.doc.attendances[i].attendance_date = cur_frm.doc.attendance_date
			}
			cur_frm.refresh_field('attendances')
		}
		else{
			console.log("New")
		}
	},

	refresh: function(frm) {
		frm.set_df_property("attendance_date", "read_only", frm.doc.__islocal ? 0 : 1);
	},

	setup_queries: function() {
		var me = this;
		this.frm.set_query("department", "departments", function() {
			if(me.frm.doc.department) {
				 return{
					filters:{ 
								'name' : ["!=", "Management"]
							
							}
						}
			} 
		});
	}


});


frappe.ui.form.on("CVS Employee Attendance", {

	out_time: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	if (child.out_time != 0){
		if (parseFloat(child.in_time) >= parseFloat(child.out_time)) {
			frappe.msgprint(__("InTime  Should Be Lesser Than OutTime."));
		}
	var startDate = "01/01/2018 " + child.in_time;
	var endDate = "01/01/2018 " + child.out_time;
	var normal_ot = document.getElementById('normal_ot');
	var special_ot = document.getElementById('special_ot');

	// frappe.model.set_value(cdt, cdn, "total_hours", 0);
	frappe.model.set_value(cdt, cdn, "special_ot", 0);
	// frappe.model.set_value(cdt, cdn, "paid_hours", 0);
	frappe.model.set_value(cdt, cdn, "normal_ot", 0);
	frappe.call({
			method: "cvs.central_ventilation_systems.doctype.cvs_employee_attendance_and_overtime.cvs_employee_attendance_and_overtime.get_outtime",
			args: {
				"intime" : child.in_time,
				"outtime" : child.out_time
			},
			callback: function(r) {
				var out = frappe.model.sync(r.message);
				frappe.model.set_value(cdt, cdn, "out_time",out[0]['time_out'] );
				if (child.holiday == 1){
					if (child.eligible_for_overtime == 1){
						frappe.model.set_value(cdt, cdn, "special_ot", out[0]['total']);
					}
					else{
						frappe.model.set_value(cdt, cdn, "total_hours", out[0]['total']);
					}
				}
				else{
					frappe.model.set_value(cdt, cdn, "total_hours", out[0]['total']);
				}
			}
		});
	}
	},

	total_hours: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	if (child.total_hours >= 24) {
			frappe.msgprint(__("Total Hours Should Not Exceed Above 23."));
		}

	total_hours = parseFloat(child.total_hours);
	paid_hours = parseFloat(child.paid_hours);
	break_time = parseFloat(child.breaktime);
	default_paid_hrs = parseFloat(child.default_paid_hrs);

		var Total_hour = total_hours,
		    Paid_hour = paid_hours,
		    Break_hour = break_time;
		    Default_hour = default_paid_hrs

		var conversionInMinutes = hour => Math.floor(hour) * 60 + (hour - (Math.floor(hour))) * 100;
		var conversionInHours = min => Math.floor( min/60 ) + min % 60 / 100;
		var Remaining_hour = conversionInMinutes(Total_hour) - (conversionInMinutes(Paid_hour) + conversionInMinutes(Break_hour));
		tot = conversionInHours(Remaining_hour).toFixed(2);

		var overtime = conversionInMinutes(Total_hour) - conversionInMinutes(Paid_hour) - conversionInMinutes(Break_hour);
		normal_ot = conversionInHours(overtime).toFixed(2);

		var paid = conversionInMinutes(Default_hour) - conversionInMinutes(Total_hour) - conversionInMinutes(Break_hour);
		paid_hrs = conversionInHours(paid).toFixed(2);


		var diff = conversionInMinutes(Total_hour) - conversionInMinutes(Break_hour);
		diff_time = conversionInHours(diff).toFixed(2);

	//tot = convertToMs(default_paid_hrs) - (convertToMs(total_hours) + convertToMs(break_time));
	
	if (total_hours > default_paid_hrs){
		console.log("Overtime");
		if (child.eligible_for_overtime == 1) {
			console.log("Employee Eligible For Overtime");
			// normal_ot = total_hours - default_paid_hrs - break_time
			if (normal_ot > 0){
				frappe.model.set_value(cdt, cdn, "normal_ot", normal_ot );
			}
			// paid = default_paid_hrs - (total_hours - break_time);
			if (paid_hrs > 0){
				frappe.model.set_value(cdt, cdn, "paid_hours",  paid_hrs);
			}
			else{
				frappe.model.set_value(cdt, cdn, "paid_hours", default_paid_hrs );
			}
		}
		else {
			console.log("Employee Ineligible For Overtime");
		}
	}
	else {
		frappe.model.set_value(cdt, cdn, "paid_hours", diff_time);
		frappe.model.set_value(cdt, cdn, "normal_ot", 0);

	}
	},

	in_time: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	if (child.in_time != 0){
		if (parseFloat(child.in_time) >= parseFloat(child.out_time)) {
			frappe.msgprint(__("InTime  Should Be Lesser Than OutTime."));
		}
		var in_time = "01/01/2018 " + child.in_time;
		var office_in_time = "01/01/2018 " + child.default_in;
		frappe.call({
			method: "cvs.central_ventilation_systems.doctype.cvs_employee_attendance_and_overtime.cvs_employee_attendance_and_overtime.get_intime",
			args: {
				"intime" : child.in_time,
				"default_in" : child.default_in
			},
			callback: function(r) {
				var inn = frappe.model.sync(r.message);
				frappe.model.set_value(cdt, cdn, "in_time",inn[0]['time_in'] );
				frappe.model.set_value(cdt, cdn, "latency",inn[0]['latency']);
			}
		});
	}
	},

	employee: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	attendance_date = child.attendance_date
	frappe.call({
			method: "cvs.central_ventilation_systems.doctype.cvs_employee_attendance_and_overtime.cvs_employee_attendance_and_overtime.get_emp_depart",
			args: {
				"employee" : child.employee
			},
			callback: function(r) {
				var att = frappe.model.sync(r.message);
				frappe.model.set_value(cdt, cdn, "in_time",att[0]['in_time'] );
				frappe.model.set_value(cdt, cdn, "out_time", att[0]['out_time']);
				frappe.model.set_value(cdt, cdn, "paid_hours", att[0]['paid_hrs']);
				frappe.model.set_value(cdt, cdn, "breaktime", att[0]['break_time']);
				frappe.model.set_value(cdt, cdn, "eligible_for_overtime", att[0]['eligible_for_overtime']);
				frappe.model.set_value(cdt, cdn, "employee_name", att[0]['employee_name']);
				frappe.model.set_value(cdt, cdn, "department", att[0]['department']);
				frappe.model.set_value(cdt, cdn, "default_paid_hrs", att[0]['paid_hrs']);

			}
		});
	},
});
