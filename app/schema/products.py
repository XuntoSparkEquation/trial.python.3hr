from datetime import datetime, timedelta
from email import utils as email_utils
from typing import Optional, Any

from pydantic import BaseModel, constr, confloat, PositiveInt, validator, conset

# Minimal expiration time, 30 days with 5 second as precision
MINIMAL_EXPIRATION = timedelta(days=30) - timedelta(seconds=5)

Name = constr(max_length=50)
Rating = confloat(ge=0, le=10)
CategoryID = int
BrandID = int


class ProductCreateSchema(BaseModel):
    """
    Defines schema and validation for creation request.
    """
    name: Name
    rating: Rating
    featured: Optional[bool]

    receipt_date: Optional[datetime]
    expiration_date: Optional[datetime]

    brand: BrandID
    categories: conset(CategoryID, min_items=1, max_items=5)

    items_in_stock: PositiveInt

    @validator("receipt_date", "expiration_date", pre=True)
    def parse_rfc_1123_datetime(cls, date: Any):
        """
        Parse string value as date in RFC 1123 format.
        @param date: date with unknown type, will be processed if string. Otherwise validator is skipped.
        @return: datetime object or string (if unable to parse as RFC 1123 formatted string)
        """
        if isinstance(date, str):
            parsed_datetime = email_utils.parsedate_to_datetime(date)
            if parsed_datetime is None:
                return date
            return parsed_datetime
        return date

    @validator("expiration_date")
    def validate_expiration_date(cls, expiration_date: datetime):
        """
        Makes sure expiration date is valid (according to acceptance criteria 3).
        Throws ValueError if expiration date in less then defined by MINIMAL_EXPIRATION.

        @param expiration_date: expiration date
        @return: expiration date if it is valid
        """
        today = datetime.utcnow()

        if expiration_date:
            time_to_expire = expiration_date - today
            if time_to_expire < MINIMAL_EXPIRATION:
                raise ValueError(f"can't set expiration in less then {MINIMAL_EXPIRATION} days")

        return expiration_date


class ProductUpdateSchema(ProductCreateSchema):
    """
    Defines schema and validation for update request.
    Mostly makes all fields optional (like Partial in Typescript).
    """
    name: Optional[Name]
    rating: Optional[Rating]

    brand: Optional[BrandID]
    categories: Optional[conset(CategoryID, min_items=1, max_items=5)]

    items_in_stock: Optional[PositiveInt]
