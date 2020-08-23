from datetime import datetime
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

    @staticmethod
    @validator("expiration_date")
    def validate_expiration_date(cls, v):
        today = datetime.utcnow()

        if v.expiration_date:
            time_to_expire = v.expiration_date - today
            if time_to_expire.days < MINIMAL_EXPIRATION_DAYS:
                raise ValueError(f"can't set expiration in less then ${MINIMAL_EXPIRATION_DAYS} days")

        return v.expiration_date
