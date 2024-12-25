from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from xero_client import get_tenants, get_invoices
from token_storage import load_refresh_token
from consulta_invoice import query_invoice

app = FastAPI()

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar plantillas
templates = Jinja2Templates(directory="app/templates")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboards/main.html", {"request": request})


########## GRUPOS EN INVOICE's ##############
#Agrupar por Emisor (Proveedor/Cliente):
def group_by_emisor(invoices):
    grouped = {}
    for invoice in invoices:
        emisor = invoice["Contact"]["Name"] if "Contact" in invoice else "Unknown"
        grouped[emisor] = grouped.get(emisor, 0) + invoice["Total"]
    return grouped

#Agrupar por Categoría (Tipo de Factura):
def group_by_category(invoices):
    grouped = {}
    for invoice in invoices:
        category = invoice["Type"]
        grouped[category] = grouped.get(category, 0) + invoice["Total"]
    return grouped



@app.post("/fetch-dashboard-data", response_class=JSONResponse)
async def fetch_dashboard_data(
    tenant_id: str = Form(...),
    data_type: str = Form(...),
    start_date: str = Form(None),
    end_date: str = Form(None)
):
    global last_processed_data  # Declara que usaremos la variable global
    try:
        if data_type == "invoices":
            data = query_invoice()  # Consulta tus datos de Xero

            # Agrupa los datos
            grouped_by_emisor = group_by_emisor(data["Invoices"])
            grouped_by_category = group_by_category(data["Invoices"])

            # Agrega los datos agrupados al JSON de respuesta
            data["GroupedByEmisor"] = grouped_by_emisor
            data["GroupedByCategory"] = grouped_by_category

        else:
            raise HTTPException(status_code=400, detail="Unsupported data type")

        # Actualizar los datos procesados
        last_processed_data = data

        return JSONResponse(content={"data": data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/data")
async def get_data():
    # Simula la consulta original a Xero
    from consulta_invoice import query_invoice  # Asegúrate de tener esta función correctamente implementada
    
    try:
        # Recupera la data original directamente
        raw_data = query_invoice()

        # Devuelve solo los datos originales
        return JSONResponse(content=raw_data, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



"""@app.get("/api/data")
async def get_data():
    global last_processed_data
    if not last_processed_data:
        return JSONResponse(content={"error": "No data available"}, status_code=404)
    return JSONResponse(content=last_processed_data)"""
