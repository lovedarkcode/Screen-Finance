"""Stock Pydantic schemas (mirror the frontend's stock.service.js shape)."""
from pydantic import BaseModel, Field


class StockOut(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float = Field(alias="changePercent")
    date: str
    marketStatus: str
    exchange: str
    country: str

    model_config = {"populate_by_name": True}


class MetricOut(BaseModel):
    label: str
    value: str


class ChartPointOut(BaseModel):
    month: str
    price: float
    volume: int


class QuarterRowOut(BaseModel):
    label: str
    values: list[str]


class QuartersOut(BaseModel):
    columns: list[str]
    rows: list[QuarterRowOut]


class PeerOut(BaseModel):
    name: str
    symbol: str
    price: float
    changePercent: float
