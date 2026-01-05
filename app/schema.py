import strawberry
from typing import List, Optional
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Ticker, Price
from app.auth import create_access_token, IsAuthenticated

# --- Types ---
@strawberry.type
class PriceType:
    date: date
    close_price: float
    volume: int

@strawberry.type
class TickerType:
    symbol: str
    name: str
    sector: str
    prices: List[PriceType]

    # Computed Field: On-the-fly technical analysis
    @strawberry.field
    def simple_moving_average(self, period: int = 5) -> Optional[float]:
        if not self.prices or len(self.prices) < period:
            return None
        # Sort by date descending
        sorted_prices = sorted(self.prices, key=lambda x: x.date, reverse=True)
        recent_prices = [p.close_price for p in sorted_prices[:period]]
        return sum(recent_prices) / period

@strawberry.type
class AuthToken:
    access_token: str
    token_type: str

# --- Inputs ---
@strawberry.input
class PriceInput:
    date: date
    close_price: float
    volume: int

# --- Query ---
@strawberry.type
class Query:
    @strawberry.field
    async def get_ticker(self, symbol: str) -> Optional[TickerType]:
        async for session in get_db():
            # Join Ticker with Prices efficiently
            query = select(Ticker).options(selectinload(Ticker.prices)).where(Ticker.symbol == symbol)
            result = await session.execute(query)
            return result.scalars().first()
        return None

    @strawberry.field
    async def get_all_tickers(self) -> List[TickerType]:
        async for session in get_db():
            query = select(Ticker).options(selectinload(Ticker.prices))
            result = await session.execute(query)
            return result.scalars().all()

# --- Mutation ---
@strawberry.type
class Mutation:
    @strawberry.field
    async def login(self, username: str) -> AuthToken:
        # Simulating user verification (In real app, check DB password)
        if username == "admin":
            token = create_access_token({"sub": username})
            return AuthToken(access_token=token, token_type="bearer")
        raise Exception("Invalid credentials")

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def add_market_data(self, symbol: str, name: str, sector: str, prices: List[PriceInput]) -> TickerType:
        async for session in get_db():
            # Check if ticker exists
            query = select(Ticker).where(Ticker.symbol == symbol)
            result = await session.execute(query)
            ticker = result.scalars().first()

            if not ticker:
                ticker = Ticker(symbol=symbol, name=name, sector=sector)
                session.add(ticker)
                await session.flush() # get ID

            # Add prices
            for p in prices:
                new_price = Price(ticker_id=ticker.id, date=p.date, close_price=p.close_price, volume=p.volume)
                session.add(new_price)
            
            await session.commit()
            
            # Re-fetch to return full object
            query = select(Ticker).options(selectinload(Ticker.prices)).where(Ticker.symbol == symbol)
            result = await session.execute(query)
            return result.scalars().first()

schema = strawberry.Schema(query=Query, mutation=Mutation)