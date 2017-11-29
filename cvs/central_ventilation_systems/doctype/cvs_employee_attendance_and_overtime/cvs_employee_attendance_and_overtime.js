// Copyright (c) 2017, sanjay.kumar@herculesglobal.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CVS Employee Attendance and Overtime', {
	setup: function(frm) {
		//console.log(cur_frm.get_docfield("attendances"));
		frm.get_docfield("attendances").allow_bulk_edit = 1;
		
	},
	refresh: function(frm) {

	}


});


frappe.ui.form.on("CVS Employee Attendance", {
	
	out_time: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	console.log("Test");
	var startDate = "01/01/2018 " + child.in_time;
	var endDate = "01/01/2018 " + child.out_time;
	var normal_ot = document.getElementById('normal_ot');
	var special_ot = document.getElementById('special_ot');
	console.log(startDate);
	console.log(child.holiday);
	if (child.holiday == 1){
		if (child.eligible_for_overtime == 1){
			frappe.model.set_value(cdt, cdn, "special_ot", moment(endDate).diff(moment(startDate),"seconds") / 3600);
		}
		else{
			frappe.model.set_value(cdt, cdn, "total_hours", moment(endDate).diff(moment(startDate),"seconds") / 3600);
		}
	}
	else{
		frappe.model.set_value(cdt, cdn, "total_hours", moment(endDate).diff(moment(startDate),"seconds") / 3600);
	}
	
	},


	total_hours: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	if (child.total_hours > 8.00){
		console.log("Overtime");
		if (child.eligible_for_overtime == 1) {
			console.log("Employee Eligible For Overtime");
			frappe.model.set_value(cdt, cdn, "normal_ot", child.total_hours - 8.00 );
		/*	query: "cvs.central_ventilation_systems.doctype.cvs_employee_attendance_and_overtime.get_attendance_settings"
			console.log(query);*/

		}
		else {
			console.log("Employee Ineligible For Overtime");
		}

	}
	else {
		console.log("Normal");
	}
	},


	in_time: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	if (child.in_time){
		console.log(in_time);
		var in_time = "01/01/2018 " + child.in_time;
		var office_in_time = "01/01/2018 " + child.default_in;
		console.log("in_time",in_time);
		console.log("office_in_time",office_in_time);
		frappe.model.set_value(cdt, cdn, "latency", moment(office_in_time).diff(moment(in_time),"seconds") / 3600);

	}

	},
	
});
