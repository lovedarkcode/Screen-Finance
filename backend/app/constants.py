"""Project-wide constants and enums."""
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"


class StockSector(str, Enum):
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    CONSUMER = "Consumer"
    ENERGY = "Energy"
    INDUSTRIAL = "Industrial"
    UTILITIES = "Utilities"


CACHE_TTL_SHORT = 60
CACHE_TTL_MEDIUM = 60 * 15
CACHE_TTL_LONG = 60 * 60 * 24

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25
