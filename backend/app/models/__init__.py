# Import all models here so Alembic's env.py can discover them
# when it does `from app.models import *` or `import app.models`.

from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.buyer import Buyer
from app.models.crop import Crop, CropUnit
from app.models.market import Market, MarketType
from app.models.market_price import MarketPrice
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus
from app.models.recommendation import Recommendation
from app.models.transaction_interest import TransactionInterest, InterestStatus

__all__ = [
    "User", "UserRole",
    "Farmer",
    "Buyer",
    "Crop", "CropUnit",
    "Market", "MarketType",
    "MarketPrice",
    "BuyerRequirement", "RequirementStatus",
    "Recommendation",
    "TransactionInterest", "InterestStatus",
]
