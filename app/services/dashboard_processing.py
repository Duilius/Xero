from app.services.data_processing import (
    group_by_emisor,
    group_by_date,
    group_by_contact,
    analyze_due_dates,
)


# Funciones para procesar cada dashboard
def process_summary_dashboard(data):
    """
    Procesa el dashboard de resumen.
    """
    grouped_by_emisor = group_by_emisor(data["Invoices"])
    grouped_by_date = group_by_date(data["Invoices"])
    total_invoices = len(data["Invoices"])
    total_amount = sum(invoice["Total"] for invoice in data["Invoices"])
    total_taxes = sum(invoice["TotalTax"] for invoice in data["Invoices"])

    return {
        "GroupedByEmisor": grouped_by_emisor,
        "GroupedByDate": grouped_by_date,
        "TotalInvoices": total_invoices,
        "TotalAmount": total_amount,
        "TotalTaxes": total_taxes,
    }


def process_contact_dashboard(data):
    """
    Procesa el dashboard por contacto.
    """
    grouped_by_contact = group_by_contact(data["Invoices"])
    total_contacts = len(grouped_by_contact)

    return {
        "GroupedByContact": grouped_by_contact,
        "TotalContacts": total_contacts,
    }


def process_due_dashboard(data):
    """
    Procesa el dashboard por fecha de vencimiento.
    """
    due_analysis = analyze_due_dates(data["Invoices"])

    return {
        "DueDateAnalysis": due_analysis,
    }
