import frappe
from frappe import _
from frappe.utils import flt
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice


def on_delivery_note_submit(doc, method=None):
	if flt(doc.grand_total) >= 50000 and not doc.get("eway_bill_no"):
		frappe.throw(_("E-Way Bill No is mandatory for Delivery Notes of ₹50,000 or more."))

	sinv = make_sales_invoice(doc.name)
	sinv.docstatus = 0
	sinv.insert(ignore_permissions=True)

	accounts_users = frappe.get_all(
		"Has Role",
		filters={"role": "Accounts User", "parenttype": "User"},
		pluck="parent",
	)
	for user in set(accounts_users or ["Administrator"]):
		if frappe.db.exists("User", user) and frappe.db.get_value("User", user, "enabled"):
			frappe.get_doc({
				"doctype": "Notification Log",
				"for_user": user,
				"type": "Alert",
				"document_type": "Sales Invoice",
				"document_name": sinv.name,
				"subject": _("Draft Sales Invoice {0} created from Delivery Note {1}").format(sinv.name, doc.name),
				"email_content": _("Draft Sales Invoice {0} was auto-created upon submission of Delivery Note {1}.").format(sinv.name, doc.name),
			}).insert(ignore_permissions=True)


def validate_delivery_note(doc, method=None):
	if flt(doc.grand_total) >= 50000 and not doc.get("eway_bill_no"):
		frappe.throw(_("E-Way Bill No is mandatory for Delivery Notes of ₹50,000 or more."))


def validate_sales_invoice_price_lock(doc, method=None):
	if "Sales Manager" in frappe.get_roles(frappe.session.user):
		return

	for row in doc.get("items") or []:
		if not row.get("sales_order"):
			continue
		so_rate = None
		if row.get("so_detail"):
			so_rate = frappe.db.get_value("Sales Order Item", row.so_detail, "rate")
		if so_rate is None and row.get("item_code"):
			so_rate = frappe.db.get_value(
				"Sales Order Item",
				{"parent": row.sales_order, "item_code": row.item_code},
				"rate",
			)
		if so_rate is not None and flt(row.rate, 2) != flt(so_rate, 2):
			frappe.throw(
				_("Row #{0}: Rate {1} for Item {2} differs from Sales Order {3} rate {4}. Sales Manager role required to override.").format(
					row.idx, row.rate, row.item_code, row.sales_order, so_rate
				)
			)
