// Copyright (c) 2016, sanjay.kumar@herculesglobal.com and contributors
// For license information, please see license.txt

frappe.query_reports["CVS Statement of Accounts"] = {
	"filters": [
 		{
 			"fieldname":"company",
 			"label": __("Company"),
 			"fieldtype": "Link",
 			"options": "Company",
 			"default": frappe.defaults.get_user_default("Company")
 		},

		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"reqd":1,
			"options": "Customer",
		},
		{
			"fieldname":"report_date",
			"label": __("As on Date"),
			"fieldtype": "Date",
			"default": get_today()
		},
		{
			"fieldtype": "Break",
		},
		{
			"fieldname":"ageing_based_on",
			"label": __("Ageing Based On"),
			"fieldtype": "Select",
			//"options": 'Posting Date' + NEWLINE + 'Due Date',
			"options": 'Posting Date',
			"default": "Posting Date"
		},
		{
			"fieldname":"range1",
			"label": __("Ageing Range 1"),
			"fieldtype": "Int",
			"default": "30",
			"reqd": 1
		},
		{
			"fieldname":"range2",
			"label": __("Ageing Range 2"),
			"fieldtype": "Int",
			"default": "60",
		},
		{
		
			"fieldname":"range3",
			"label": __("Ageing Range 3"),
			"fieldtype": "Int",
			"default": "90",
			"reqd": 1
		}
	]
}
