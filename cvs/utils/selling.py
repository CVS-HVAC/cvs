# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from frappe import _
from frappe.model.utils import get_fetch_values
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_cvs_production_order(source_name, target_doc=None):
	def set_missing_values(source, target):
		add_sales_order_details(source, target)
		add_product(source, target)
		add_required_items(source, target)
		add_operations(source, target)

	def add_sales_order_details(source, target):
		if source.po_no:
			if target.po_no:
				target_po_no = target.po_no.split(", ")
				target_po_no.append(source.po_no)
				target.po_no = ", ".join(list(set(target_po_no))) if len(target_po_no) > 1 else target_po_no[0]
			else:
				target.po_no = source.po_no

		if source.project:
			if target.project:
				target_project = target.project.split(", ")
				target_project.append(source.project)
				target.po_no = ", ".join(list(set(target_project))) if len(target_project) > 1 else target_project[0]
			else:
				target.project = source.project

		if target.sales_order:
			target_sales_order = target.sales_order.split(", ")
			target_sales_order.append(source.name)
			target.sales_order = ", ".join(list(set(target_sales_order))) if len(target_sales_order) > 1 else target_sales_order[0]
		else:
			target.sales_order = source.name



	def add_product(source, target):
		from erpnext.selling.doctype.sales_order.sales_order import get_default_bom_item
		products = []
		for table in [source.items, source.packed_items]:
			for i in table:
				bom = get_default_bom_item(i.item_code)
				if bom:
					stock_qty = i.qty if i.doctype == 'Packed Item' else i.stock_qty
					products.append(dict(
						item_code= i.item_code,
						bom = bom,
						sales_order_qty = i.qty,
						produced_qty = i.qty,
						warehouse = i.warehouse,
						#pending_qty= stock_qty - flt(frappe.db.sql('''select sum(qty) from `tabProduction Order`
						#	where production_item=%s and sales_order=%s''', (i.item_code, self.name))[0][0])
					))
		target.set('products', products)

	def add_required_items(source, target):
		from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
		from erpnext.selling.doctype.sales_order.sales_order import get_default_bom_item
		required_items = []
		for i in target.products:
			bom = get_default_bom_item(i.item_code)

			item_dict = get_bom_items_as_dict(bom, source.company, qty=i.produced_qty,
				fetch_exploded = True) #self.use_multi_level_bom)

			for item in sorted(item_dict.values(), key=lambda d: d['idx']):
				required_items.append(dict(
					item_code = item.item_code,
					required_qty = item.qty,
					transferred_qty = item.qty,
					bom = bom,
					source_warehouse = item.source_warehouse or item.default_warehouse
				))

		target.set('required_items', required_items)


	def add_operations(source, target):
		operations = []
		for i in target.products:
			#if self.use_multi_level_bom:
			#	bom_list = frappe.get_doc("BOM", self.bom_no).traverse_tree()
			#else:
			#	bom_list = [self.bom_no]
			bom_list = frappe.get_doc("BOM", i.bom).traverse_tree()		
			operations = frappe.db.sql("""
				select 
					operation, description, workstation, idx,
					base_hour_rate as hour_rate, time_in_mins, 
					"Pending" as status, parent as bom
				from
					`tabBOM Operation`
				where
					 parent in (%s) order by idx
			"""	% ", ".join(["%s"]*len(bom_list)), tuple(bom_list), as_dict=1)

			target.set('operations', operations)


	def update_item(source, target, source_parent):
		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
		target.qty = flt(source.qty) - flt(source.delivered_qty)
		target.produced_qty = flt(source.qty) - flt(source.delivered_qty)
		target.delivered_qty = source.delivered_qty
		target.so_qty = source.qty
		item = frappe.db.get_value("Item", target.item_code, ["item_group", "selling_cost_center"], as_dict=1)
		target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center") \
			or item.selling_cost_center \
			or frappe.db.get_value("Item Group", item.item_group, "default_cost_center")

	target_doc = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "CVS Production Order",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		#"Sales Order Item": {
		#	"doctype": "CVS Production Order Product",
		#	"field_map": {
		#		"rate": "rate",
		#		"name": "so_detail",
		#		"parent": "against_sales_order",
		#	},
		#	"postprocess": update_item,
			#"condition": lambda doc: abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
		#},
		#"Sales Taxes and Charges": {
		#	"doctype": "Sales Taxes and Charges",
		#	"add_if_empty": True
		#},
		#"Sales Team": {
		#	"doctype": "Sales Team",
		#	"add_if_empty": True
		#}
	}, target_doc, set_missing_values)
	#}, target_doc)

	return target_doc


@frappe.whitelist()
def get_production_order_items(sales_order):
	'''Returns items with BOM that already do not have a linked production order'''
	from erpnext.selling.doctype.sales_order.sales_order import get_default_bom_item
	so_doc = frappe.get_doc("Sales Order", sales_order)
	items = []

	for table in [so_doc.items, so_doc.packed_items]:
		for i in table:
			bom = get_default_bom_item(i.item_code)
			if bom:
				stock_qty = i.qty if i.doctype == 'Packed Item' else i.stock_qty
				items.append(dict(
					item_code= i.item_code,
					bom = bom,
					warehouse = i.warehouse,
					pending_qty= stock_qty - flt(frappe.db.sql('''select sum(qty) from `tabProduction Order`
						where production_item=%s and sales_order=%s''', (i.item_code, self.name))[0][0])
				))

	return items

@frappe.whitelist()
def make_cvs_production_orders(items, sales_order, company, project=None):
	'''Make Production Orders against the given Sales Order for the given `items`'''
	items = json.loads(items).get('items')
	out = []

	for i in items:
		production_order = frappe.get_doc(dict(
			doctype='Production Order',
			production_item=i['item_code'],
			bom_no=i['bom'],
			qty=i['pending_qty'],
			company=company,
			sales_order=sales_order,
			project=project,
			fg_warehouse=i['warehouse']
		)).insert()
		production_order.set_production_order_operations()
		production_order.save()
		out.append(production_order)

	return [p.name for p in out]

