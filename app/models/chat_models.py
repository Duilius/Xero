from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# Tabla de Clientes
class ChatClient(Base):
    __tablename__ = 'chat_clients'
    id = Column(Integer, primary_key=True)
    business_name = Column(String(255), nullable=False)
    abn = Column(String(50), nullable=False, unique=True)
    contact_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone_number = Column(String(20), nullable=False)
    address = Column(String(255))
    status = Column(String(20), nullable=False)


# Tabla de Impuestos
class ChatTax(Base):
    __tablename__ = 'chat_taxes'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    rate = Column(Float, nullable=False)
    description = Column(String(255))

# Tabla de Declaraciones Tributarias
class ChatTaxReturn(Base):
    __tablename__ = 'chat_tax_returns'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('chat_clients.id'), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    gst_collected = Column(Float, nullable=False)
    gst_paid = Column(Float, nullable=False)
    net_tax_payable = Column(Float, nullable=False)
    lodgment_date = Column(Date)
    client = relationship("ChatClient", back_populates="tax_returns")

ChatClient.tax_returns = relationship("ChatTaxReturn", order_by=ChatTaxReturn.id, back_populates="client")

# Tabla de Facturas Emitidas
class ChatIssuedInvoice(Base):
    __tablename__ = 'chat_issued_invoices'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('chat_clients.id'), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount_excl_gst = Column(Float, nullable=False)
    gst = Column(Float, nullable=False)
    amount_incl_gst = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)

# Tabla de Logs de Actividad
class ChatActivityLog(Base):
    __tablename__ = 'chat_activity_logs'
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    timestamp = Column(Date, nullable=False)
    ip_address = Column(String(50))

# Tabla de Stock de Productos
class ChatProductStock(Base):
    __tablename__ = 'chat_product_stock'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('chat_clients.id'), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity_in_stock = Column(Integer, nullable=False)
    restock_level = Column(Integer, nullable=False)
    last_updated = Column(Date, nullable=False)
    client = relationship("ChatClient", back_populates="product_stock")

ChatClient.product_stock = relationship("ChatProductStock", order_by=ChatProductStock.id, back_populates="client")

# Tabla de Pagos Realizados
class ChatPayment(Base):
    __tablename__ = 'chat_payments'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('chat_clients.id'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('chat_received_invoices.id'), nullable=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    reference = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    client = relationship("ChatClient", back_populates="payments")

ChatClient.payments = relationship("ChatPayment", order_by=ChatPayment.id, back_populates="client")

# Tabla de Facturas Recibidas
class ChatReceivedInvoice(Base):
    __tablename__ = 'chat_received_invoices'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('chat_clients.id'), nullable=False)
    supplier_name = Column(String(255), nullable=False)  # Proveedor
    abn_supplier = Column(String(50), nullable=True)  # ABN del proveedor
    invoice_number = Column(String(50), unique=True, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Float, nullable=False)
    gst_amount = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # Paid, Pending, Overdue, etc.
    client = relationship("ChatClient", back_populates="received_invoices")

ChatClient.received_invoices = relationship("ChatReceivedInvoice", order_by=ChatReceivedInvoice.id, back_populates="client")