from datetime import datetime
from zoneinfo import ZoneInfo

# En app/utils/date_utils.py
def format_local_datetime(utc_str):
    """Solo convertir a formato legible, sin forzar zona horaria"""
    dt = datetime.fromisoformat(utc_str)
    return dt.strftime("%Y-%m-%d %I:%M %p UTC")  # Mantenemos UTC