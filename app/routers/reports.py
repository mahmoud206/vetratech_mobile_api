from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Dict, Any
from app.database import db
from app.utils.pdf import generate_full_report_pdf
from app.models import ReportRequest, FullReportResponse


router = APIRouter()

# Constants
EXCLUDED_CONTACTS = [
    "د/ محمد صيدلية بيش",
    "عيادة الأنعام - الإدارة",
    "مؤسسة علي محمد غروي البيطرية",
    "صيدليه علي محمد غروي",
    "عيادة الانعام الظبية"
]

DATABASE_MAP = {
    "khamis": "Elanam-KhamisMushit",
    "baish": "Elanam-Baish",
    "zapia": "Elanam-Zapia"
}


@router.post("/full-report", response_model=FullReportResponse)
async def generate_full_report(request: ReportRequest):
    try:
        # 1. Connect to MongoDB
        db_name = DATABASE_MAP.get(request.db_option)
        if not db_name:
            raise HTTPException(status_code=400, detail="Invalid database option")

        database = db.connect(db_name)

        # 2. Fetch all reports concurrently
        payment_report = await _get_payment_report(database, request.start_date, request.end_date)
        clinic_report = await _get_clinic_report(database, request.start_date, request.end_date)
        sales_report = await _get_sales_report(database, request.start_date, request.end_date)

        # 3. Generate PDF
        pdf_bytes = await generate_full_report_pdf(
            payment_data=payment_report,
            clinic_data=clinic_report,
            sales_data=sales_report,
            start_date=request.start_date,
            end_date=request.end_date,
            db_name=db_name
        )

        return {
            "success": True,
            "payment_report": payment_report,
            "clinic_report": clinic_report,
            "sales_report": sales_report,
            "pdf_bytes": pdf_bytes.decode('latin1')  # Convert to string for JSON
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    finally:
        db.close()


async def _get_payment_report(db, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Get payment totals grouped by method and type (incoming/outgoing)"""
    pipeline = [
        {
            "$match": {
                "createdAt": {"$gte": start_date, "$lte": end_date},
                "isDeleted": False
            }
        },
        {
            "$group": {
                "_id": {
                    "method": "$method",
                    "isOutgoing": "$isOutgoing"
                },
                "totalAmount": {"$sum": "$amount"},
                "transactionCount": {"$sum": 1}
            }
        },
        {
            "$project": {
                "method": "$_id.method",
                "isOutgoing": "$_id.isOutgoing",
                "totalAmount": 1,
                "transactionCount": 1,
                "_id": 0
            }
        }
    ]
    return await db["Payment"].aggregate(pipeline).to_list(None)


async def _get_clinic_report(db, start_date: datetime, end_date: datetime) -> Dict[str, float]:
    """Get clinic revenue with special handling for 'لارج' services"""
    pipeline = [
        {
            "$match": {
                "createdAt": {"$gte": start_date, "$lte": end_date},
                "isDeleted": False,
                "isResolved": True
            }
        },
        {"$unwind": "$services"},
        {
            "$addFields": {
                "isLarge": {
                    "$regexMatch": {
                        "input": "$services.serviceName",
                        "regex": "لارج"
                    }
                },
                "serviceRevenue": {
                    "$multiply": ["$services.price", "$services.quantity"]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "totalRevenue": {"$sum": "$serviceRevenue"},
                "largeServicesRevenue": {
                    "$sum": {
                        "$cond": [
                            "$isLarge", "$serviceRevenue", 0
                        ]
                    }
                },
                "normalServicesRevenue": {
                    "$sum": {
                        "$cond": [
                            "$isLarge", 0, "$serviceRevenue"
                        ]
                    }
                }
            }
        }
    ]

    result = await db["Sale"].aggregate(pipeline).to_list(None)
    return result[0] if result else {
        "totalRevenue": 0,
        "largeServicesRevenue": 0,
        "normalServicesRevenue": 0
    }


async def _get_sales_report(db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get sales revenue and profit, excluding specific contacts"""
    pipeline = [
        {
            "$match": {
                "createdAt": {"$gte": start_date, "$lte": end_date},
                "contactName": {"$nin": EXCLUDED_CONTACTS},
                "isDeleted": False
            }
        },
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": None,
                "totalRevenue": {
                    "$sum": {
                        "$multiply": ["$items.pricePerUnit", "$items.quantity"]
                    }
                },
                "totalProfit": {"$sum": "$items.profit"},
                "topProducts": {
                    "$push": {
                        "productName": "$items.productName",
                        "revenue": {
                            "$multiply": ["$items.pricePerUnit", "$items.quantity"]
                        },
                        "profit": "$items.profit"
                    }
                }
            }
        },
        {
            "$project": {
                "totalRevenue": 1,
                "totalProfit": 1,
                "topProducts": {
                    "$slice": [
                        {
                            "$sortArray": {
                                "input": "$topProducts",
                                "sortBy": {"revenue": -1}
                            }
                        },
                        5  # Return top 5 products
                    ]
                },
                "_id": 0
            }
        }
    ]

    result = await db["Sale"].aggregate(pipeline).to_list(None)
    return result[0] if result else {
        "totalRevenue": 0,
        "totalProfit": 0,
        "topProducts": []
    }