from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

# Crear un router para agrupar las rutas del dashboard
dashboard_router = APIRouter()

@dashboard_router.post("/fetch-dashboard-data", response_class=HTMLResponse)
async def fetch_dashboard_data(
    tenant_id: str = Form(...),
    data_type: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    # Simular datos para el dashboard
    data_html = f"""
    <h2>Data for {data_type}</h2>
    <p>Tenant ID: {tenant_id}</p>
    <p>Date Range: {start_date} to {end_date}</p>
    <table>
        <thead>
            <tr><th>Field</th><th>Value</th></tr>
        </thead>
        <tbody>
            <tr><td>Example 1</td><td>Value 1</td></tr>
            <tr><td>Example 2</td><td>Value 2</td></tr>
        </tbody>
    </table>
    """
    return data_html
