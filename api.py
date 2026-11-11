import os
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    total = database.count_quotes()
    if total == 0:
        try:
            database.sync_sheets_to_sqlite()
        except Exception:
            pass
    yield

app = FastAPI(
    title="Quote Monitor Public API",
    description="API pública para consulta e sincronização em tempo real das cotações armazenadas em SQLite.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuoteItem(BaseModel):
    id: Optional[int] = None
    datetime: str = Field(..., description="Data e hora no formato ISO (YYYY-MM-DD HH:MM:SS)")
    currency: str = Field(..., description="Símbolo da moeda (ex: USD, EUR, BTC)")
    quote_value: float = Field(..., description="Valor numérico da cotação em Reais (BRL)")
    percent_change: float = Field(..., description="Variação percentual da cotação")
    raw_date: Optional[str] = Field(None, description="Data original da planilha")
    raw_quote: Optional[str] = Field(None, description="Texto original do valor")
    raw_percent: Optional[str] = Field(None, description="Texto original do percentual")

class QuoteCreate(BaseModel):
    currency: str = Field(..., example="USD")
    quote_value: float = Field(..., example=5.45)
    percent_change: float = Field(..., example=0.25)
    datetime: Optional[str] = Field(None, example="2026-11-04 15:30:00")

class SyncRequest(BaseModel):
    sheets_url: Optional[str] = Field(None, description="URL pública customizada da planilha XLSX")

class SyncResponse(BaseModel):
    status: str
    source: str
    processed_records: int
    note: Optional[str] = None

class QuotesListResponse(BaseModel):
    total: int
    data: List[QuoteItem]

@app.get("/", tags=["Geral"])
def root():
    return {
        "message": "Quote Monitor Public API está online",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "list_quotes": "/api/quotes",
            "latest_quotes": "/api/quotes/latest",
            "currencies": "/api/currencies",
            "sync": "/api/quotes/sync"
        }
    }

@app.get("/health", tags=["Geral"])
def health_check():
    total_records = database.count_quotes()
    return {
        "status": "healthy",
        "database": database.DB_FILE,
        "total_records": total_records,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/currencies", response_model=List[str], tags=["Cotações"])
def get_currencies():
    return database.get_available_currencies()

@app.get("/api/quotes", response_model=QuotesListResponse, tags=["Cotações"])
def list_quotes(
    currency: Optional[str] = Query(None, description="Filtrar por moeda (ex: USD, EUR, BTC)"),
    start_date: Optional[str] = Query(None, description="Data inicial no formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Data final no formato YYYY-MM-DD"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Limite máximo de registros")
):
    try:
        results = database.get_quotes(
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return {
            "total": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar cotações: {str(e)}")

@app.get("/api/quotes/latest", response_model=List[QuoteItem], tags=["Cotações"])
def get_latest_quotes():
    try:
        return database.get_latest_quotes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter últimas cotações: {str(e)}")

@app.post("/api/quotes/sync", response_model=SyncResponse, tags=["Sincronização"])
def sync_spreadsheet(body: Optional[SyncRequest] = None):
    custom_url = body.sheets_url if body else None
    result = database.sync_sheets_to_sqlite(sheets_url=custom_url)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

@app.post("/api/quotes", response_model=QuoteItem, status_code=status.HTTP_201_CREATED, tags=["Cotações"])
def create_quote(quote: QuoteCreate):
    dt_str = quote.datetime or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    currency = quote.currency.strip().upper()

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quotes (datetime, currency, quote_value, percent_change, raw_date, raw_quote, raw_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(datetime, currency) DO UPDATE SET
                quote_value = excluded.quote_value,
                percent_change = excluded.percent_change
        """, (
            dt_str,
            currency,
            quote.quote_value,
            quote.percent_change,
            dt_str,
            str(quote.quote_value),
            f"{quote.percent_change:+.2f}%"
        ))
        conn.commit()

        cursor.execute("SELECT * FROM quotes WHERE datetime = ? AND currency = ?", (dt_str, currency))
        row = cursor.fetchone()
        return dict(row)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
