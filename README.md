# O2C Ext (`o2c_ext`) — Anantchem ERPNext Extensions

ERPNext extension app on `erp.localhost` for **Anantchem**, extending standard ERPNext.

## Setup, Seed Data, Migration & Verification

1. Ensure `o2c_ext` is installed on `erp.localhost` with `"erpnext"` in `required_apps` (`apps/erpnext` and `apps/frappe` remain untouched).
   
2. Run migrations and clear cache:
   
         cd ~/frappe-bench
         bench --site erp.localhost migrate
         bench --site erp.localhost clear-cache


Run the standard ERPNext O2C flow (Lead / Opportunity -> Quotation -> Sales Order -> credit check block & resolution -> Pick List -> Delivery Note partial deliveries -> Sales Invoice -> Payment Entry), inspect Accounts Receivable (30, 60, 90) and the Sales Order Connections tab, and export fixtures whenever Custom Fields, Workflows, or Notifications change:

      cd ~/frappe-bench
      bench --site erp.localhost export-fixtures

