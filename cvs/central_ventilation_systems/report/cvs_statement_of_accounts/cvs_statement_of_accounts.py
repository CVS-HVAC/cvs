# Copyright (c) 2013, sanjay.kumar@herculesglobal.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils import getdate, nowdate, flt, cint
from operator import itemgetter

class ReceivablePayableReport(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.filters.report_date = getdate(self.filters.report_date or nowdate())
		self.age_as_on = getdate(nowdate()) \
			if self.filters.report_date > getdate(nowdate()) \
			else self.filters.report_date

	def run(self, args):
		party_naming_by = frappe.db.get_value(args.get("naming_by")[0], None, args.get("naming_by")[1])
		return self.get_columns(party_naming_by, args), self.get_data(party_naming_by, args)

	def get_columns(self, party_naming_by, args):
		columns = [_("Posting Date") + ":Date:80", _(args.get("party_type")) + ":Link/" + args.get("party_type") + ":200"]

		if party_naming_by == "Naming Series":
			columns += [args.get("party_type") + " Name::110"]

		columns += [_("Voucher Type") + "::110", _("Voucher No") + ":Dynamic Link/"+_("Voucher Type")+":120",
			_("Due Date") + ":Date:80"]

		if args.get("party_type") == "Supplier":
			columns += [_("Bill No") + "::80", _("Bill Date") + ":Date:80"]

		credit_or_debit_note = "Credit Note" if args.get("party_type") == "Customer" else "Debit Note"

		for label in ("Invoiced Amount", "Paid Amount", credit_or_debit_note, "Outstanding Amount"):
			columns.append({
				"label": label,
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			})

		columns += [_("Age (Days)") + ":Int:80"]

		if not "range1" in self.filters:
			self.filters["range1"] = "30"
		if not "range2" in self.filters:
			self.filters["range2"] = "60"
		if not "range3" in self.filters:
			self.filters["range3"] = "90"
			
		for label in ("0-{range1}".format(**self.filters),
			"{range1}-{range2}".format(**self.filters),
			"{range2}-{range3}".format(**self.filters),
			"{range3}-{above}".format(range3=self.filters.range3, above=_("Above"))):
				columns.append({
					"label": label,
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120
				})

		columns.append({
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		})
		if args.get("party_type") == "Customer":
			columns += [
				_("Territory") + ":Link/Territory:80", 
				_("Customer Group") + ":Link/Customer Group:120"
			]
		if args.get("party_type") == "Supplier":
			columns += [_("Supplier Type") + ":Link/Supplier Type:80"]
			
		columns += [_("PDC Amount") + ":Currency:80"]
		columns += [_("Balance") + ":Data:80"]
		columns.append(_("Remarks") + "::200")
		if args.get("party_type") == "Customer":
			columns +=[_("po_no") + "::80", _("po_date") + ":Date:80"]
		
		return columns

	def get_data(self, party_naming_by, args):
		from erpnext.accounts.utils import get_currency_precision
		currency_precision = get_currency_precision() or 2
		dr_or_cr = "debit" if args.get("party_type") == "Customer" else "credit"

		voucher_details = self.get_voucher_details(args.get("party_type"))

		future_vouchers = self.get_entries_after(self.filters.report_date, args.get("party_type"))

		if not self.filters.get("company"):
			self.filters["company"] = frappe.db.get_single_value('Global Defaults', 'default_company')

		company_currency = frappe.db.get_value("Company", self.filters.get("company"), "default_currency")
		
		return_entries = self.get_return_entries(args.get("party_type"))

		data = []
		for gle in self.get_entries_till(self.filters.report_date, args.get("party_type")):
			if self.is_receivable_or_payable(gle, dr_or_cr, future_vouchers):
				outstanding_amount, credit_note_amount = self.get_outstanding_amount(gle, 
					self.filters.report_date, dr_or_cr, return_entries, currency_precision)
				if abs(outstanding_amount) > 0.1/10**currency_precision:
					row = [gle.posting_date, gle.party]

					# customer / supplier name
					if party_naming_by == "Naming Series":
						row += [self.get_party_name(gle.party_type, gle.party)]

					# get due date
					due_date = voucher_details.get(gle.voucher_no, {}).get("due_date", "")

					row += [gle.voucher_type, gle.voucher_no, due_date]

					# get supplier bill details
					if args.get("party_type") == "Supplier":
						row += [
							voucher_details.get(gle.voucher_no, {}).get("bill_no", ""),
							voucher_details.get(gle.voucher_no, {}).get("bill_date", "")
						]

					# invoiced and paid amounts
					invoiced_amount = gle.get(dr_or_cr) if (gle.get(dr_or_cr) > 0) else 0
					paid_amt = invoiced_amount - outstanding_amount - credit_note_amount
					row += [invoiced_amount, paid_amt, credit_note_amount, outstanding_amount]

					# ageing data
					entry_date = due_date if self.filters.ageing_based_on == "Due Date" else gle.posting_date
					row += get_ageing_data(cint(self.filters.range1), cint(self.filters.range2),
						cint(self.filters.range3), self.age_as_on, entry_date, outstanding_amount)

					if self.filters.get(scrub(args.get("party_type"))):
						row.append(gle.account_currency)
					else:
						row.append(company_currency)

					# customer territory / supplier type
					if args.get("party_type") == "Customer":
						row += [self.get_territory(gle.party), self.get_customer_group(gle.party)]
					if args.get("party_type") == "Supplier":
						row += [self.get_supplier_type(gle.party)]

					# pdc and balance
					row += [0.00, 0.00]

					inv_remarks = voucher_details.get(gle.voucher_no, {}).get("remarks", "")
					remarks = [("{0} {1}".format(gle.remarks.replace("No Remarks","") if gle.remarks else "", inv_remarks)).strip()]
					row.append(remarks)
					#po_no = voucher_details.get(gle.voucher_no, {}).get("po_no", "")
					#po_no = voucher_details.get(gle.voucher_no, {}).get("po_date", "")
					data.append(row)


		data += self.get_pdc_data(party_naming_by,args)
		data = sorted(data, key=itemgetter(0))
		self.add_balance(data, args.get("party_type"))
		frappe.msgprint("data:{0}".format(data))
		return data


	def get_pdc_data(self, party_naming_by, args):
		company_currency = frappe.db.get_value("Company", self.filters.get("company"), "default_currency")
		data = []
		for pdc in self.get_pdc_entries_till(self.filters.report_date, args.get("party_type")):
			row = [getdate(pdc.posting_date), pdc.party]

			# customer / supplier name
			if party_naming_by == "Naming Series":
				row += [self.get_party_name(pdc.party_type, pdc.party)]

			# get due date
			#due_date = voucher_details.get(pdc.voucher_no, {}).get("due_date", "")

			row += [pdc.voucher_type, pdc.voucher_no, getdate(pdc.due_date)]
			
			# bill number and date
			if args.get("party_type") == "Supplier":
				row += [pdc.bill_no, getdate(pdc.bill_date)]

			# invoice amount 
			row += [0.00, 0.00, 0.00]

			# ageing data
			row += [0.00, 0.00, 0.00, 0.00, 0.00]

			if self.filters.get(scrub(args.get("party_type"))):
				row.append(pdc.account_currency)
			else:
				row.append(company_currency)

			# customer territory / supplier type
			if args.get("party_type") == "Customer":
				row += [self.get_territory(pdc.party)]
			elif args.get("party_type") == "Supplier":
				row += [self.get_supplier_type(pdc.party)]
			else:
				row += [""]
			
			# pdc amount
			row += [pdc.pdc_amount]

			# balance
			row += [00.00]

			# remark
			row.append(pdc.remarks)

			data.append(row)
		return data

	def add_balance(self, data, party_type):
		balance = 0.00
		#balance = prev balance + outstanding_amount
		if party_type == "Customer":
			for d in data:
				#balance = prev balance + outstanding_amount - pdc_amount
				#balance = balance + (d[7] - d[-3])
				balance = balance + flt(d[7])
				d[-2] = flt(balance,2)

		elif party_type == "Supplier":
			for d in data:
				#balance = balance + (d[9] - d[-3])
				balance += flt(d[9])
				d[-2] = flt(balance,2)



	def get_entries_after(self, report_date, party_type):
		# returns a distinct list
		return list(set([(e.voucher_type, e.voucher_no) for e in self.get_gl_entries(party_type)
			if getdate(e.posting_date) > report_date]))

	def get_entries_till(self, report_date, party_type):
		# returns a generator
		return (e for e in self.get_gl_entries(party_type)
			if getdate(e.posting_date) <= report_date)

	def get_pdc_entries_till(self, report_date, party_type):
		# returns a generator
		return (e for e in self.get_pdc_entries(party_type)
			if getdate(e.posting_date) <= report_date)


	def is_receivable_or_payable(self, gle, dr_or_cr, future_vouchers):
		return (
			# advance
			(not gle.against_voucher) or

			# against sales order/purchase order
			(gle.against_voucher_type in ["Sales Order", "Purchase Order"]) or

			# sales invoice/purchase invoice
			(gle.against_voucher==gle.voucher_no and gle.get(dr_or_cr) > 0) or

			# entries adjusted with future vouchers
			((gle.against_voucher_type, gle.against_voucher) in future_vouchers)
		)
		
	def get_return_entries(self, party_type):
		doctype = "Sales Invoice" if party_type=="Customer" else "Purchase Invoice"
		return [d.name for d in frappe.get_all(doctype, filters={"is_return": 1, "docstatus": 1})]	

	def get_outstanding_amount(self, gle, report_date, dr_or_cr, return_entries, currency_precision):
		payment_amount, credit_note_amount = 0.0, 0.0
		reverse_dr_or_cr = "credit" if dr_or_cr=="debit" else "debit"
		
		for e in self.get_gl_entries_for(gle.party, gle.party_type, gle.voucher_type, gle.voucher_no):
			if getdate(e.posting_date) <= report_date and e.name!=gle.name:
				amount = flt(e.get(reverse_dr_or_cr)) - flt(e.get(dr_or_cr))
				if e.voucher_no not in return_entries:
					payment_amount += amount
				else:
					credit_note_amount += amount
					
		outstanding_amount = flt((flt(gle.get(dr_or_cr)) - flt(gle.get(reverse_dr_or_cr)) \
			- payment_amount - credit_note_amount), currency_precision)
		credit_note_amount = flt(credit_note_amount, currency_precision)
		
		return outstanding_amount, credit_note_amount

	def get_party_name(self, party_type, party_name):
		return self.get_party_map(party_type).get(party_name, {}).get("customer_name" if party_type == "Customer" else "supplier_name") or ""

	def get_territory(self, party_name):
		return self.get_party_map("Customer").get(party_name, {}).get("territory") or ""
		
	def get_customer_group(self, party_name):
		return self.get_party_map("Customer").get(party_name, {}).get("customer_group") or ""

	def get_supplier_type(self, party_name):
		return self.get_party_map("Supplier").get(party_name, {}).get("supplier_type") or ""

	def get_party_map(self, party_type):
		if not hasattr(self, "party_map"):
			if party_type == "Customer":
				select_fields = "name, customer_name, territory, customer_group"
			elif party_type == "Supplier":
				select_fields = "name, supplier_name, supplier_type"
			
			self.party_map = dict(((r.name, r) for r in frappe.db.sql("select {0} from `tab{1}`"
				.format(select_fields, party_type), as_dict=True)))

		return self.party_map

	def get_voucher_details(self, party_type):
		voucher_details = frappe._dict()

		if party_type == "Customer":
			for si in frappe.db.sql("""select name, due_date,'po_no' as po_no,'po_date' as po_date,
				replace(remarks, 'No Remarks','') as remarks
				from `tabSales Invoice` where docstatus=1""", as_dict=1):
					voucher_details.setdefault(si.name, si)

		if party_type == "Supplier":
			for pi in frappe.db.sql("""select name, due_date, bill_no, bill_date,
				replace(remarks, 'No Remarks','') as remarks
				from `tabPurchase Invoice` where docstatus=1""", as_dict=1):
					voucher_details.setdefault(pi.name, pi)

		return voucher_details

	def get_gl_entries(self, party_type):
		if not hasattr(self, "gl_entries"):
			conditions, values = self.prepare_conditions(party_type)

			if self.filters.get(scrub(party_type)):
				select_fields = "debit_in_account_currency as debit, credit_in_account_currency as credit"
			else:
				select_fields = "debit, credit"

			self.gl_entries = frappe.db.sql("""select name, posting_date, account, party_type, party, 
				voucher_type, voucher_no, against_voucher_type, against_voucher, 
				account_currency, remarks, {0}
				from `tabGL Entry`
				where docstatus < 2 and party_type=%s and (party is not null and party != '') {1}
				order by posting_date, party"""
				.format(select_fields, conditions), values, as_dict=True)

		return self.gl_entries

	def get_pdc_entries(self, party_type):
		if not hasattr(self, "pdc_entries"):

			cost_center = ""
			party = ""
			party_type_field = scrub(party_type)

			if self.filters.get(scrub(party_type)):
				select_fields = "doc.allocated_amount as pdc_amount"
			else:
				select_fields = "doc.allocated_amount as pdc_amount"


			if self.filters.get(party_type_field):
				party = "and ent.party='%s'"%self.filters.get(party_type_field)

				
			self.pdc_entries = frappe.db.sql("""		
				select 
				ent.name,
				ent.posting_date, 
				ent.party,
				-- doc.account,
				ent.party_type,
				doc.parenttype as voucher_type,
				doc.parent as voucher_no,
				'' as against_voucher_type,
				'' as against_voucher,
				ent.reference_date as due_date,
				ent.paid_from_account_currency as account_currency,
				ent.reference_no as bill_no,
				ent.reference_date as bill_date,
				ent.remarks         
				{select_fields}
				from `tabPayment Entry` as ent
				inner join `tabPayment Entry Reference` as doc on (doc.parent = ent.name)
				where doc.docstatus = 0
				and ent.reference_date > ent.posting_date
				and ent.company='{company}' 
				{cost_center} 
				{party}
				"""
				.format(select_fields=select_fields, 
				company=self.filters.company,
				cost_center=cost_center,
				party=party
				), as_dict=True)

		frappe.msgprint("pdc{0}".format(self.pdc_entries))
		return self.pdc_entries


	def prepare_conditions(self, party_type):
		conditions = [""]
		values = [party_type]

		party_type_field = scrub(party_type)

		if self.filters.company:
			conditions.append("company=%s")
			values.append(self.filters.company)

		if self.filters.cost_center:
			conditions.append("cost_center=%s")
			values.append(self.filters.cost_center)


		if self.filters.get(party_type_field):
			conditions.append("party=%s")
			values.append(self.filters.get(party_type_field))

		return " and ".join(conditions), values

	def get_gl_entries_for(self, party, party_type, against_voucher_type, against_voucher):
		if not hasattr(self, "gl_entries_map"):
			self.gl_entries_map = {}
			for gle in self.get_gl_entries(party_type):
				if gle.against_voucher_type and gle.against_voucher:
					self.gl_entries_map.setdefault(gle.party, {})\
						.setdefault(gle.against_voucher_type, {})\
						.setdefault(gle.against_voucher, [])\
						.append(gle)

		return self.gl_entries_map.get(party, {})\
			.get(against_voucher_type, {})\
			.get(against_voucher, [])

def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	return ReceivablePayableReport(filters).run(args)

def get_ageing_data(first_range, second_range, third_range, age_as_on, entry_date, outstanding_amount):
	# [0-30, 30-60, 60-90, 90-above]
	outstanding_range = [0.0, 0.0, 0.0, 0.0]

	if not (age_as_on and entry_date):
		return [0] + outstanding_range

	age = (getdate(age_as_on) - getdate(entry_date)).days or 0
	index = None
	for i, days in enumerate([first_range, second_range, third_range]):
		if age <= days:
			index = i
			break

	if index is None: index = 3
	outstanding_range[index] = outstanding_amount

	return [age] + outstanding_range
