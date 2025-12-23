# Trade Opportunities - Stock Market Analysis API (India)

A FastAPI service that returns markdown sector analysis reports using Indian stock data (NSE/BSE) from `stock.indianapi.in`.

## Features
- POST `/analyze` accepts sector names and returns markdown reports.
- Market sentiment, average change, gainers/losers, and key stocks.
- Indian currency (₹) formatting.
- Market hours awareness (NSE): shows a banner when closed.


## Requirements
- Python 3.11+
- Dependencies from `requirements.txt`
- Indian Stock API key (`X-Api-Key`)

## Setup
1) Install dependencies:
```bash
pip install -r requirements.txt
```
2) Set your API key (replace with your key):
```bash
setx INDIAN_STOCK_API_KEY "sk-live-XXXXX"
```
The code currently uses the provided key in `market_service.py`.

## Run the server
```bash
python main.py
```

## Endpoints
- `/docs` — Demo URL
- `GET /` — service status
- `GET /health` — health check
- `GET /sectors/suggestions` — common sector names (India NSE/BSE)
- `POST /analyze` — generate markdown reports

### POST /analyze
Request:
```json
{
  "sectors": ["Technology", "Financial Services"]
}
```
Response: `text/plain` markdown combining each sector’s report.

## Sectors supported (examples)
- Technology, Healthcare, Financial Services, Energy, Consumer Discretionary, Consumer Staples, Industrials, Materials, Real Estate, Utilities, Communication Services.

## Notes on data
- Data source: `https://stock.indianapi.in/stock` with `X-Api-Key`.
- Tries both NSE and BSE.
- Handles price fields across nested shapes (priceInfo/data/quote/currentPrice).

