# O2C Ext (`o2c_ext`) — Anantchem ERPNext Extensions

## Setup, Seed Data, Migration & Verification
1. Ensure `o2c_ext` is installed on `erp.localhost` with `"erpnext"` in `required_apps` (`apps/erpnext` and `apps/frappe` remain untouched).
2. Run migrations and clear cache:
   ```bash
   cd ~/frappe-bench
   bench --site erp.localhost migrate
   bench --site erp.localhost clear-cache
