DB_SCHEMA = {
    "tables": {
        "chat_clients": ["id", "business_name", "abn", "contact_name", "email", "phone_number", "status"],
        "chat_issued_invoices": ["id", "client_id", "invoice_date", "due_date", "amount_excl_gst", "gst", "amount_incl_gst", "status"],
        "chat_tax_returns": ["id", "client_id", "period_start", "period_end", "gst_collected", "gst_paid", "net_tax_payable", "lodgment_date"],
        "chat_sold_products": ["id", "client_id", "product_id", "quantity", "unit_price", "sale_date", "total_price", "gst"],
        "chat_product_stock": ["id", "client_id", "product_name", "quantity_in_stock", "restock_level", "last_updated"],
        "chat_payments": ["id", "client_id", "invoice_id", "payment_date", "amount", "payment_method", "status"],
        "chat_employees": ["id", "client_id", "first_name", "last_name", "email", "position", "salary", "hire_date"],
        "chat_salaries": ["id", "employee_id", "pay_date", "gross_amount", "net_amount", "tax_withheld"],
        "chat_products": ["id", "client_id", "product_name", "sku", "stock_quantity", "price", "gst_applicable"],
        "chat_transactions": ["id", "client_id", "transaction_date", "description", "amount", "transaction_type"],
        "chat_received_invoices": ["id", "client_id", "supplier_name", "abn_supplier", "invoice_number", "issue_date", "due_date", "total_amount", "gst_amount", "status"],
        "chat_taxes": ["id", "name", "rate", "description"],
        "chat_activity_logs": ["id", "user_email", "action", "timestamp", "ip_address"]
    },
    "relationships": [
        ("chat_issued_invoices.client_id", "chat_clients.id"),
        ("chat_tax_returns.client_id", "chat_clients.id"),
        ("chat_sold_products.client_id", "chat_clients.id"),
        ("chat_sold_products.product_id", "chat_products.id"),
        ("chat_payments.invoice_id", "chat_received_invoices.id"),
        ("chat_salaries.employee_id", "chat_employees.id"),
        ("chat_product_stock.client_id", "chat_clients.id"),
        ("chat_transactions.client_id", "chat_clients.id"),
        ("chat_employees.client_id", "chat_clients.id")
    ]
}