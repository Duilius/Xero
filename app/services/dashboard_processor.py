from app.services.dashboard_processing import group_by_emisor, group_by_date, group_by_contact, analyze_due_dates

def process_summary_dashboard(data):
    grouped_by_emisor = group_by_emisor(data["Invoices"])
    grouped_by_date = group_by_date(data["Invoices"])  # Asegúrate de que esta función devuelve datos válidos
    return {
        "GroupedByEmisor": grouped_by_emisor,
        "GroupedByDate": grouped_by_date,
        "TotalInvoices": len(data["Invoices"]),
        "TotalAmount": sum(invoice.get("Total", 0) for invoice in data["Invoices"]),
        "TotalTaxes": sum(invoice.get("TotalTax", 0) for invoice in data["Invoices"]),
    }


def process_contact_dashboard(data):
    grouped_by_contact = group_by_contact(data["Invoices"])  # Verifica que esta función funciona correctamente
    return {
        "GroupedByContact": grouped_by_contact,
        "TotalContacts": len(grouped_by_contact),
    }


def process_due_dashboard(data):
    due_date_analysis = analyze_due_dates(data["Invoices"])
    return {
        "DueDateAnalysis": due_date_analysis,
    }
