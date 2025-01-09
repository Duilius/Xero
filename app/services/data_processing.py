def group_by_emisor(invoices):
    """
    Agrupa las facturas por emisor.
    """
    grouped = {}
    for invoice in invoices:
        emisor = invoice["Contact"]["Name"]
        total = invoice["Total"]
        grouped[emisor] = grouped.get(emisor, 0) + total
    return grouped


def group_by_date(invoices):
    """
    Agrupa las facturas por fecha.
    """
    grouped = {}
    for invoice in invoices:
        date = invoice["DateString"]
        total = invoice["Total"]
        grouped[date] = grouped.get(date, 0) + total
    return grouped


def group_by_contact(invoices):
    """
    Agrupa las facturas por contacto.
    """
    grouped = {}
    for invoice in invoices:
        contact = invoice["Contact"]["Name"]
        total = invoice["Total"]
        grouped[contact] = grouped.get(contact, 0) + total
    return grouped


def analyze_due_dates(invoices):
    """
    Analiza las facturas por fechas de vencimiento.
    """
    due_analysis = {"dueSoon": 0, "overdue": 0}
    for invoice in invoices:
        due_date = invoice["DueDateString"]
        status = invoice["Status"]
        if status == "AUTHORISED":
            # Puedes agregar lógica específica aquí
            due_analysis["dueSoon"] += invoice["Total"]
        elif status == "OVERDUE":
            due_analysis["overdue"] += invoice["Total"]
    return due_analysis