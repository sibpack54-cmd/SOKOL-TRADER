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
            for item in data.get('marketdata', {}).get('data', []):
                if len(item) > 12 and item[12] is not None:
                    return float(item[12])
            return 0.0
