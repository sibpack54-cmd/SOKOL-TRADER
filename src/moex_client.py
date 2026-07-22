import aiohttp

class MOEXClient:
    BASE_URL = "https://iss.moex.com/iss"
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def get_current_price(self, ticker: str) -> float:
        url = f"{self.BASE_URL}/engines/stock/markets/shares/securities/{ticker}.json"
        async with self.session.get(url) as response:
            data = await response.json()
            columns = data.get('marketdata', {}).get('columns', [])
            rows = data.get('marketdata', {}).get('data', [])
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                if row_dict.get('BOARDID') == 'TQBR':
                    last = row_dict.get('LAST')
                    if last is not None:
                        return float(last)
                    market_price = row_dict.get('MARKETPRICE')
                    if market_price is not None:
                        return float(market_price)
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                last = row_dict.get('LAST')
                if last is not None:
                    return float(last)
            
            return 0.0
