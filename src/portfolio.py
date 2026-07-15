"""
Портфель — JSON-based локальное хранилище
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Position:
    ticker: str
    qty: int
    entry_price: float
    entry_date: str
    signal_id: str
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    status: str

class Portfolio:
    def __init__(self, portfolio_path: str):
        self.portfolio_path = portfolio_path
        self.data = self._load_portfolio()

    def _load_portfolio(self) -> Dict:
        """Загрузить портфель из JSON"""
        if not os.path.exists(self.portfolio_path):
            os.makedirs(os.path.dirname(self.portfolio_path), exist_ok=True)
            return {
                "positions": [],
                "capital": 100000.0,
                "risk_per_trade": 0.02
            }
        
        with open(self.portfolio_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_portfolio(self):
        """Сохранить портфель в JSON"""
        with open(self.portfolio_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_position(self, ticker: str, qty: int, price: float, signal_id: str, 
                     stop: float, tp1: float, tp2: float):
        """Добавить позицию"""
        position = Position(
            ticker=ticker,
            qty=qty,
            entry_price=price,
            entry_date=datetime.now().isoformat(),
            signal_id=signal_id,
            stop_loss=stop,
            take_profit_1=tp1,
            take_profit_2=tp2,
            status="active"
        )
        
        self.data["positions"].append(asdict(position))
        self._save_portfolio()

    def close_position(self, ticker: str, price: float) -> Optional[float]:
        """Закрыть позицию и вернуть P&L"""
        for i, pos in enumerate(self.data["positions"]):
            if pos["ticker"] == ticker and pos["status"] == "active":
                entry_price = pos["entry_price"]
                qty = pos["qty"]
                pnl = (price - entry_price) * qty
                
                self.data["positions"][i]["status"] = "closed"
                self._save_portfolio()
                
                return pnl
        
        return None

    def get_portfolio(self) -> List[Dict]:
        """Получить все позиции"""
        return self.data["positions"]

    def get_pnl(self) -> Dict:
        """Получить общий P&L"""
        total_pnl = 0.0
        positions_pnl = []

        for pos in self.data["positions"]:
            if pos["status"] == "closed":
                entry_price = pos["entry_price"]
                exit_price = pos.get("exit_price", entry_price)
                qty = pos["qty"]
                pnl = (exit_price - entry_price) * qty
                total_pnl += pnl
                positions_pnl.append({
                    "ticker": pos["ticker"],
                    "pnl": pnl
                })

        return {
            "total_pnl": total_pnl,
            "positions_pnl": positions_pnl
        }

    def update_capital(self, new_capital: float):
        """Обновить капитал"""
        self.data["capital"] = new_capital
        self._save_portfolio()

    def get_capital(self) -> float:
        """Получить текущий капитал"""
        return self.data.get("capital", 100000.0)
