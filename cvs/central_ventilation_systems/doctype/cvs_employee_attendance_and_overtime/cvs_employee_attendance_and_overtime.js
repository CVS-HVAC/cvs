// Copyright (c) 2017, sanjay.kumar@herculesglobal.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('CVS Employee Attendance and Overtime', {

	setup: function(frm) {
		frm.get_docfield("attendances").allow_bulk_edit = 1;
		frm.set_df_property("attendance_date", "read_only", frm.doc.__islocal ? 0 : 1);
	},

	attendance_date: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		console.log(child.attendances);
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
	}
});

frappe.ui.form.on("CVS Employee Attendance", {

	out_time: function(frm, cdt, cdn) {
	var child = locals[cdt][cdn];
	var startDate = "01/01/2018 " + child.in_time;
	var endDate = "01/01/2018 " + child.out_time;
	var normal_ot = document.getElementById('normal_ot');
	var special_ot = document.getElementById('special_ot');
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
		var in_time = "01/01/2018 " + child.in_time;
		var office_in_time = "01/01/2018 " + child.default_in;
		frappe.model.set_value(cdt, cdn, "latency", moment(office_in_time).diff(moment(in_time),"seconds") / 3600);
	}
	},
});
