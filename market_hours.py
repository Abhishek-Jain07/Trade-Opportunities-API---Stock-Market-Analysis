from datetime import datetime
import pytz


class MarketHours:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.market_open = 9
        self.market_open_min = 15
        self.market_close = 15
        self.market_close_min = 30
    
    def is_market_open(self) -> bool:
        ist_now = datetime.now(self.ist)
        weekday = ist_now.weekday()
        
        if weekday >= 5:
            return False
        
        current_time = ist_now.hour * 60 + ist_now.minute
        open_time = self.market_open * 60 + self.market_open_min
        close_time = self.market_close * 60 + self.market_close_min
        
        return open_time <= current_time <= close_time
    
    def get_market_status_message(self) -> str:
        if self.is_market_open():
            return None
        return "ℹ️ Market closed. Prices reflect last trading session."

