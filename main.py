from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime
import re
import logging

from market_service import MarketDataService
from report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trade Opportunities API",
    description="A FastAPI service that analyzes NSE/BSE sector performance and generates readable market insights."
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

market_service = MarketDataService()
report_generator = ReportGenerator(market_service)


class SectorRequest(BaseModel):
    sectors: List[str] = Field(..., min_length=1, max_length=10)
    
    @field_validator('sectors')
    @classmethod
    def validate_sector_name(cls, v):
        validated = []
        for sector in v:
            if not sector or not str(sector).strip():
                raise ValueError('Sector name cannot be empty')
            cleaned = re.sub(r'[^a-zA-Z0-9\s\-&]', '', str(sector).strip())
            if len(cleaned) < 2:
                raise ValueError('Sector name must be at least 2 characters')
            if len(cleaned) > 100:
                raise ValueError('Sector name cannot exceed 100 characters')
            validated.append(cleaned.title())
        return validated


@app.get("/")
async def root():
    return {"status": "active", "service": "Sector Analysis API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/analyze", response_class=PlainTextResponse)
@limiter.limit("10/minute")
async def analyze_sectors(
    request: Request,
    sector_request: SectorRequest
):
    try:
        results = []
        
        for sector in sector_request.sectors:
            try:
                market_data = await market_service.get_sector_data(sector)
                report = report_generator.generate_report(sector, market_data)
                results.append(report)
            except Exception as e:
                logger.error(f"Error analyzing sector {sector}: {str(e)}")
                error_msg = f"## Error analyzing {sector}\n\nUnable to retrieve market data: {str(e)}\n\n**Note:** Please verify that the Indian Stock Market API is accessible and the API key is correctly configured.\n"
                results.append(error_msg)
        
        combined_report = "\n\n---\n\n".join(results)
        return combined_report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/sectors/suggestions")
async def get_sector_suggestions():
    common_sectors = [
        "Technology",
        "Healthcare",
        "Financial Services",
        "Energy",
        "Consumer Discretionary",
        "Consumer Staples",
        "Industrials",
        "Materials",
        "Real Estate",
        "Utilities",
        "Communication Services"
    ]
    return {
        "suggestions": common_sectors,
        "exchange": "NSE/BSE",
        "region": "India"
    }



