def format_number(value):
    """Format number with thousands separator and 2 decimal places."""
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value