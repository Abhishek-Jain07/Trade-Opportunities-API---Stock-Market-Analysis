import aiohttp
import asyncio
import json
from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self):
        self.api_key = "sk-live-Li8C3zJV6oyJpxCG81vQ91qYbuCL5SwnL5W7rpYg"
        self.base_url = "https://stock.indianapi.in"
        self.timeout = 10
        self.cache = {}
        self.cache_ttl = 300
    
    async def get_sector_data(self, sector: str) -> Dict:
        cache_key = sector.lower()
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        try:
            data = await self._fetch_market_data(sector)
            self.cache[cache_key] = (data, datetime.now())
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch market data: {str(e)}")
    
    async def _fetch_market_data(self, sector: str) -> Dict:
        sector_mapping = {
            "Technology": ["INFY", "TCS", "WIPRO", "HCLTECH", "TECHM"],
            "Healthcare": ["SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN", "AUROPHARMA"],
            "Financial Services": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN"],
            "Energy": ["RELIANCE", "ONGC", "IOC", "BPCL", "GAIL"],
            "Consumer Discretionary": ["TITAN", "MARUTI", "BAJAJ-AUTO", "M&M", "HEROMOTOCO"],
            "Consumer Staples": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
            "Industrials": ["LT", "BHEL", "SIEMENS", "ABB", "THERMAX"],
            "Materials": ["TATASTEEL", "JSWSTEEL", "ULTRACEMCO", "SHREECEM", "ACC"],
            "Real Estate": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "SOBHA"],
            "Utilities": ["NTPC", "POWERGRID", "TATAPOWER", "ADANIPOWER", "TORNTPOWER"],
            "Communication Services": ["BHARTIARTL", "RELIANCE", "IDEA", "VODAFONE", "TATACOMM"]
        }
        
        sector_lower = sector.lower()
        tickers = None
        
        for key, value in sector_mapping.items():
            if key.lower() == sector_lower:
                tickers = value
                break
        
        if not tickers:
            tickers = ["RELIANCE", "TCS", "HDFCBANK"]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            tasks = [self._get_stock_data(session, ticker) for ticker in tickers[:5]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for r in results:
            if isinstance(r, dict) and not isinstance(r, Exception):
                if r.get("price", 0) > 0:
                    valid_results.append(r)
                else:
                    logger.debug(f"Filtered out {r.get('symbol')} - price is 0")
            elif isinstance(r, Exception):
                logger.error(f"Exception fetching stock data: {str(r)}")
        
        if not valid_results:
            logger.warning(f"No valid stock data found for sector: {sector}")
            return self._generate_fallback_data(sector)
        
        return {
            "sector": sector,
            "tickers": valid_results,
            "timestamp": datetime.now().isoformat(),
            "summary": self._calculate_summary(valid_results)
        }
    
    async def _get_stock_data(self, session: aiohttp.ClientSession, ticker: str) -> Dict:
        symbol = ticker.upper()
        headers = {
            "X-Api-Key": self.api_key
        }
        
        exchanges = ["NSE", "BSE"]
        
        for exchange in exchanges:
            try:
                url = f"{self.base_url}/stock"
                params = {
                    "name": symbol,
                    "exchange": exchange
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                        except Exception as e:
                            logger.warning(f"Failed to parse JSON for {ticker} from {exchange}: {str(e)}")
                            continue
                        
                        if isinstance(data, dict):
                            current_price = None
                            previous_close = None
                            high = None
                            low = None
                            volume = None
                            market_cap = None
                            percent_change = 0
                            
                            price_info = data.get("priceInfo") or data.get("data") or data.get("quote") or {}
                            if isinstance(price_info, dict):
                                current_price = price_info.get("lastPrice") or price_info.get("ltp") or price_info.get("price") or price_info.get("currentPrice")
                                previous_close = price_info.get("previousClose") or price_info.get("prevClose") or price_info.get("close")
                                high = price_info.get("high") or price_info.get("dayHigh") or price_info.get("highPrice")
                                low = price_info.get("low") or price_info.get("dayLow") or price_info.get("lowPrice")
                                volume = (
                                    price_info.get("volume")
                                    or price_info.get("tradedVolume")
                                    or price_info.get("totalVolume")
                                    or price_info.get("totalTradedVolume")
                                )
                                market_cap = price_info.get("marketCap") or price_info.get("marketCapitalization") or price_info.get("mcap")
                                percent_change = price_info.get("percentChange") or price_info.get("changePercent") or 0
                            
                            if not current_price:
                                current_price_obj = data.get("currentPrice", {})
                                if isinstance(current_price_obj, dict):
                                    current_price = current_price_obj.get(exchange) or current_price_obj.get("NSE") or current_price_obj.get("BSE")
                                else:
                                    current_price = current_price_obj
                            
                            if not current_price:
                                current_price = data.get("lastPrice") or data.get("ltp") or data.get("price")
                            
                            if not percent_change:
                                percent_change = data.get("percentChange", 0)
                            
                            if not previous_close:
                                stock_technical = data.get("stockTechnicalData", {})
                                if isinstance(stock_technical, list) and len(stock_technical) > 0:
                                    stock_technical = stock_technical[0]
                                
                                if isinstance(stock_technical, dict):
                                    previous_close = stock_technical.get("previousClose") or stock_technical.get("prevClose") or stock_technical.get("close")
                                    if not high:
                                        high = stock_technical.get("high") or stock_technical.get("dayHigh") or stock_technical.get("highPrice")
                                    if not low:
                                        low = stock_technical.get("low") or stock_technical.get("dayLow") or stock_technical.get("lowPrice")
                                    if not volume:
                                        volume = (
                                            stock_technical.get("volume")
                                            or stock_technical.get("tradedVolume")
                                            or stock_technical.get("totalVolume")
                                            or stock_technical.get("totalTradedVolume")
                                        )
                            
                            if not high:
                                high = data.get("yearHigh") or data.get("high") or data.get("dayHigh")
                            if not low:
                                low = data.get("yearLow") or data.get("low") or data.get("dayLow")
                            
                            if not market_cap:
                                key_metrics = data.get("keyMetrics", {})
                                if isinstance(key_metrics, dict):
                                    market_cap = key_metrics.get("marketCap") or key_metrics.get("marketCapitalization") or key_metrics.get("mcap")
                            
                            def safe_float(value, default=None):
                                if value is None or value == "":
                                    return default
                                try:
                                    if isinstance(value, str):
                                        cleaned = value.replace(",", "").strip()
                                        return float(cleaned) if cleaned else default
                                    return float(value)
                                except (ValueError, TypeError):
                                    return default
                            
                            def safe_int(value, default=0):
                                if value is None or value == "":
                                    return default
                                try:
                                    if isinstance(value, str):
                                        cleaned = value.replace(",", "").strip()
                                        return int(float(cleaned)) if cleaned else default
                                    return int(float(value))
                                except (ValueError, TypeError):
                                    return default
                            
                            current_price_num = safe_float(current_price)
                            
                            if current_price_num is None or current_price_num <= 0:
                                continue
                            
                            previous_close_num = safe_float(previous_close)
                            if previous_close_num is None or previous_close_num <= 0:
                                percent_change_num = safe_float(percent_change)
                                if percent_change_num is not None:
                                    previous_close_num = current_price_num / (1 + percent_change_num / 100) if percent_change_num != -100 else current_price_num
                                else:
                                    previous_close_num = current_price_num
                            
                            high_val = safe_float(high, default=0.0)
                            low_val = safe_float(low, default=0.0)
                            volume_val = safe_int(volume)
                            market_cap_val = safe_int(market_cap)
                            
                            change = current_price_num - previous_close_num
                            percent_change_num = safe_float(percent_change)
                            change_percent = percent_change_num if percent_change_num is not None else (change / previous_close_num * 100) if previous_close_num > 0 else 0
                            
                            logger.info(f"Successfully fetched data for {ticker} from {exchange}: price={current_price_num}")
                            return {
                                "symbol": ticker,
                                "price": round(current_price_num, 2),
                                "change": round(change, 2),
                                "changePercent": round(change_percent, 2),
                                "volume": volume_val,
                                "marketCap": market_cap_val,
                                "high": round(high_val, 2) if high_val > 0 else 0,
                                "low": round(low_val, 2) if low_val > 0 else 0
                            }
                    elif response.status == 401:
                        logger.warning(f"Authentication failed for {ticker} on {exchange}")
                    elif response.status == 404:
                        logger.debug(f"Stock {ticker} not found on {exchange}")
                    else:
                        response_text = await response.text()
                        logger.debug(f"Status {response.status} for {ticker} from {exchange}: {response_text[:200]}")
            except Exception as e:
                logger.debug(f"Error fetching {ticker} from {exchange}: {str(e)}")
                continue
        
        return {
            "symbol": ticker,
            "price": 0,
            "change": 0,
            "changePercent": 0,
            "volume": 0,
            "marketCap": 0,
            "high": 0,
            "low": 0
        }
    
    def _calculate_summary(self, tickers: List[Dict]) -> Dict:
        if not tickers:
            return {}
        
        prices = [t["price"] for t in tickers if t["price"] > 0]
        changes = [t["changePercent"] for t in tickers if t["changePercent"]]
        volumes = [t["volume"] for t in tickers if t["volume"] > 0]
        
        return {
            "avgPrice": sum(prices) / len(prices) if prices else 0,
            "avgChangePercent": sum(changes) / len(changes) if changes else 0,
            "totalVolume": sum(volumes),
            "gaining": len([c for c in changes if c > 0]),
            "losing": len([c for c in changes if c < 0]),
            "unchanged": len([c for c in changes if c == 0])
        }
    
    def _generate_fallback_data(self, sector: str) -> Dict:
        return {
            "sector": sector,
            "tickers": [],
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "avgPrice": 0,
                "avgChangePercent": 0,
                "totalVolume": 0,
                "gaining": 0,
                "losing": 0,
                "unchanged": 0
            },
            "note": "Limited data available"
        }
    
    def invalidate_cache(self, key: str = None):
        if key:
            cache_key = key.lower()
            if cache_key in self.cache:
                del self.cache[cache_key]
        else:
            self.cache.clear()

