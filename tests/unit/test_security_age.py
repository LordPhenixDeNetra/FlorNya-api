from datetime import date

import pytest

from app.core.security import verify_minimum_age


def test_minimum_age_13_enforced() -> None:
    dob = date.today().replace(year=date.today().year - 10)
    with pytest.raises(ValueError):
        verify_minimum_age(dob)
