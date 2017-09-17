// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.provide("cvs");
frappe.provide("cvs.utils");

$.extend(cvs, {
	toList: function(value){
		if(!$.isArray(value))
			value = [value];
		return value;
	},
	get_default_value: function(fieldname, user=null){

		// check if user has multiple permissions
		var dval = frappe.defaults.get_user_defaults(fieldname);

		// check if user has permission
		if(($.isArray(dval) && !dval[0]) || !dval){
			dval= frappe.defaults.get_user_default(fieldname);
		}

		var s_key = frappe.model.scrub(fieldname);
		// check cost_center default

		if((($.isArray(dval) && !dval[0]) || !dval) && this.user_default_cost_center){
			eval_str = 'frappe.get_doc(":Cost Center", "'+this.user_default_cost_center[0]+'").'+s_key;
		}

		// check company default
		if(($.isArray(dval) && !dval[0]) || !dval){
			var eval_str = 'frappe.get_doc(":Company", "'+cur_frm.doc.company+'").'+s_key;
			dval= eval(eval_str);

		}
		return this.toList(dval);
	},
	get_item_prev_doc: function(fieldname) {
		// prevdoc_docname
		fieldname = frappe.model.scrub(fieldname);
		var prev_doc = [];
		$.each(cur_frm.doc["items"] || [], function(i, item) {
			if (item[fieldname] && !in_list(prev_doc, item[fieldname])){
				prev_doc.push(item[fieldname]);
			}
		});
		return prev_doc;
	},
	set_item_details_if_different: function(fieldname, value) {
		var changed = false;
		for (var i=0, l=(cur_frm.doc.items || []).length; i<l; i++) {
			var row = cur_frm.doc.items[i];
			if (row[fieldname] != value) {
				frappe.model.set_value(row.doctype, row.name, fieldname, value, "Link");
				changed = true;
			}
		}
		refresh_field("items");
	},
	get_list: function(doctype, fields, filters, callback){
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: doctype,
				fields: fields,
				filters: filters
			},
			callback: function(r) {
				callback(r)
			}
		})
	},

});



