from datetime import datetime
from email import utils as email_utils
from typing import Optional

from pydantic import BaseModel, constr, confloat, PositiveInt, validator, conset

MINIMAL_EXPIRATION_DAYS = 30

Name = constr(max_length=50)
Rating = confloat(ge=0, le=10)
CategoryID = int
BrandID = int


class ProductSchema(BaseModel):
    name: Name
    rating: Rating
    featured: Optional[bool] = False

    receipt_date: Optional[datetime]
    expiration_date: Optional[datetime]

    brand: BrandID
    categories: conset(CategoryID, min_items=1, max_items=5)

    items_in_stock: PositiveInt

    @validator("receipt_date", "expiration_date", pre=True)
    def parse_rfc_1123_datetime(cls, date):
        if isinstance(date, str):
            parsed_datetime = email_utils.parsedate_to_datetime(date)
            if parsed_datetime is None:
                return date
            return parsed_datetime
        return date

    @validator("expiration_date")
    def validate_expiration_date(cls, expiration_date):
        today = datetime.utcnow()

        if expiration_date:
            time_to_expire = expiration_date - today
            if time_to_expire.days < MINIMAL_EXPIRATION_DAYS:
                raise ValueError(f"can't set expiration in less then {MINIMAL_EXPIRATION_DAYS} days")

        return expiration_date
