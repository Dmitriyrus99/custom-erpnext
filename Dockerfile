FROM frappe/erpnext:v15

WORKDIR /home/frappe/frappe-bench
USER root

COPY --chown=frappe:frappe apps/ferum_custom ./apps/ferum_custom

USER frappe
