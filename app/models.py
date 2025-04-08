from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

class ReportRequest(BaseModel):
    db_option: str  # "khamis", "baish", or "zapia"
    start_date: datetime
    end_date: datetime

class PaymentReportItem(BaseModel):
    method: str
    isOutgoing: bool
    totalAmount: float
    transactionCount: int

class ClinicReportItem(BaseModel):
    totalRevenue: float
    largeServicesRevenue: float
    normalServicesRevenue: float

class SalesReportItem(BaseModel):
    totalRevenue: float
    totalProfit: float
    topProducts: List[Dict[str, Any]]

class FullReportResponse(BaseModel):
    success: bool
    payment_report: List[PaymentReportItem]
    clinic_report: ClinicReportItem
    sales_report: SalesReportItem
    pdf_bytes: str