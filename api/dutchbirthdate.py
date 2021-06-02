import re
from datetime import date, datetime
from typing import Optional, Union

YEAR = 0
MONTH = 1
DAY = 2

FORMAT_MESSAGE = "Birthdate must be according to ISO, 10 characters: YYYY-MM-DD."


class DutchBirthDate(str):
    """
    People in the Netherlands can be born on a normal ISO date such as: 1980-12-31.
    But they can also be born on 1980-XX-XX.

    The EU signer does not understand this date of birth, but can work with "year" instead.
    The domestic signer expects these fields to be empty when there are XX-es.

    You can throw in any datetime, date, ISO date string with XX for day and month.

    This type provides a single point of definition where the date will be converted to something workable.

    https://pydantic-docs.helpmanual.io/usage/types/#custom-data-types
    """

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern="^[0-9]{4}-[0-9X]{2}-[0-9X]{2}$",
            examples=["1980-12-31", "1980-XX-XX"],
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    # Needed as attribute in the EU signer, together with date
    # Defaults to 0 so they evaluate as False.
    # 1900 - 2100
    year: int = 0

    # Needed as attribute in domestic signer
    # 1 - 12
    month: Optional[int] = None

    # Needed as attribute in domestic signer
    # 1 - 31
    day: Optional[int] = None

    def __init__(self, possible_date):
        super().__init__()

        # Happy flow: a date is given and it's easy to work with:
        try:
            converted = datetime.strptime(possible_date, "%Y-%m-%d")
            self.year = converted.year
            self.month = converted.month
            self.day = converted.day
        # Cannot convert to a date, this is more exceptional.
        except ValueError:
            # ignore case:
            possible_date = possible_date.upper()
            parts = possible_date.split("-")

            # Todo: can year be XXXX?
            self.year = int(parts[YEAR])

            # It's possible only days or only month are XX
            if parts[MONTH] != "XX":
                self.month = int(parts[MONTH])

            if parts[DAY] != "XX":
                self.day = int(parts[DAY])

    @classmethod
    def validate(cls, possible_date: Union[str, date]):

        # Be more flexible than just a string, allow to set dates and datetimes and just work(!)
        if isinstance(possible_date, date) or isinstance(possible_date, datetime):
            possible_date = date.strftime(possible_date, "%Y-%m-%d")

        if not isinstance(possible_date, str):
            raise TypeError(f"{FORMAT_MESSAGE} (must be a string or date)")

        # Any other values than X-s and any incorrect formatting.
        if not re.fullmatch(r"[0-9]{4}-[0-9X]{2}-[0-9X]{2}", possible_date):
            raise ValueError(f"{FORMAT_MESSAGE} (wrong format or invalid substitution character).")

        return cls(possible_date)

    @property
    def date(self) -> Union[int, date]:
        # Needed as attribute in the eu signer
        if not self.day or not self.month:
            return self.year

        return date(self.year, self.month, self.day)

    def __str__(self):
        return str(self.date)

    def __repr__(self):
        return str(self.date)
