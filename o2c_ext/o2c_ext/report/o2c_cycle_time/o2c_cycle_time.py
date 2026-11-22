import frappe
from frappe import _
from frappe.utils import date_diff, flt


def execute(filters=None):
	filters = filters or {}
	conditions = ["so.docstatus = 1"]
	values = []

	if filters.get("company"):
		conditions.append("so.company = %s")
		values.append(filters["company"])
	if filters.get("customer"):
		conditions.append("so.customer = %s")
		values.append(filters["customer"])

	where_clause = " AND ".join(conditions)
	orders = frappe.db.sql(
		f"""
		SELECT
			so.name AS sales_order,
			so.customer AS customer,
			so.transaction_date AS order_date,
			so.delivery_date AS so_delivery_date,
			COALESCE(SUM(soi.qty), 0) AS ordered_qty,
			COALESCE(SUM(soi.delivered_qty), 0) AS delivered_qty,
			(
				SELECT MAX(dn.posting_date)
				FROM `tabDelivery Note Item` dni
				INNER JOIN `tabDelivery Note` dn ON dn.name = dni.parent
				WHERE dni.so_detail = soi.name AND dn.docstatus = 1
			) AS last_delivery_date,
			(
				SELECT MIN(si.posting_date)
				FROM `tabSales Invoice Item` sii
				INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
				WHERE sii.sales_order = so.name AND si.docstatus = 1
			) AS invoice_date,
			(
				SELECT MAX(pe.posting_date)
				FROM `tabPayment Entry Reference` per
				INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
				INNER JOIN `tabSales Invoice Item` sii ON sii.parent = per.reference_name
				WHERE per.reference_doctype = 'Sales Invoice'
					AND sii.sales_order = so.name
					AND pe.docstatus = 1
			) AS payment_date
		FROM `tabSales Order` so
		LEFT JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE {where_clause}
		GROUP BY so.name, so.customer, so.transaction_date, so.delivery_date
		ORDER BY so.transaction_date DESC, so.name DESC
		""",
		tuple(values),
		as_dict=True,
	)

	customer_days = {}
	customer_otif_hits = {}
	customer_otif_total = {}
	enriched = []

	for row in orders:
		end_date = row.get("payment_date") or row.get("invoice_date") or row.get("last_delivery_date")
		total_days = date_diff(end_date, row["order_date"]) if (end_date and row.get("order_date")) else None
		cust = row["customer"]
		customer_otif_total[cust] = customer_otif_total.get(cust, 0) + 1

		fully_delivered = flt(row.get("delivered_qty")) >= flt(row.get("ordered_qty")) and flt(row.get("ordered_qty")) > 0
		on_time = bool(row.get("last_delivery_date") and row.get("so_delivery_date") and str(row["last_delivery_date"]) <= str(row["so_delivery_date"]))
		if fully_delivered and on_time:
			customer_otif_hits[cust] = customer_otif_hits.get(cust, 0) + 1

		if total_days is not None:
			customer_days.setdefault(cust, []).append(flt(total_days))

		row["total_days"] = total_days
		enriched.append(row)

	data = []
	for row in enriched:
		cust = row["customer"]
		days_list = customer_days.get(cust) or []
		avg_days = flt(sum(days_list) / len(days_list), 1) if days_list else None
		otif_pct = flt((customer_otif_hits.get(cust, 0) / customer_otif_total[cust]) * 100.0, 1) if customer_otif_total.get(cust) else 0.0
		row["avg_days_per_customer"] = avg_days
		row["otif_pct"] = otif_pct
		data.append(row)

	columns = [
		{"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 160},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
		{"label": _("Order Date"), "fieldname": "order_date", "fieldtype": "Date", "width": 115},
		{"label": _("Last Delivery Date"), "fieldname": "last_delivery_date", "fieldtype": "Date", "width": 135},
		{"label": _("Invoice Date"), "fieldname": "invoice_date", "fieldtype": "Date", "width": 115},
		{"label": _("Payment Date"), "fieldname": "payment_date", "fieldtype": "Date", "width": 115},
		{"label": _("Total Days"), "fieldname": "total_days", "fieldtype": "Int", "width": 105},
		{"label": _("Avg Days per Customer"), "fieldname": "avg_days_per_customer", "fieldtype": "Float", "width": 165},
		{"label": _("OTIF %"), "fieldname": "otif_pct", "fieldtype": "Percent", "width": 100},
	]
	return columns, data
