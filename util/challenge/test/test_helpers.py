import datetime
from datetime import timezone

from enforce_typing import enforce_types
import pytest

from util.challenge import helpers


@enforce_types
def test_dt_to_ut__timezone():
    # setup
    unaware_dt = datetime.datetime(2011, 8, 15, 8, 15, 12, 0)
    aware_dt = datetime.datetime(2011, 8, 15, 8, 15, 12, 0, tzinfo=timezone.utc)
    now_aware_dt = unaware_dt.replace(tzinfo=timezone.utc)
    assert aware_dt == now_aware_dt

    # can we check tzinfo ?
    assert unaware_dt.tzinfo is None
    assert aware_dt.tzinfo == timezone.utc
    assert now_aware_dt.tzinfo == timezone.utc

    # run dt_to_ut(). unaware_dt should fail, others should pass
    with pytest.raises(Exception) as e_info:
        helpers.dt_to_ut(unaware_dt)
    error_str = str(e_info.value)
    assert error_str == "must be in UTC"

    ut = helpers.dt_to_ut(aware_dt)

    ut = helpers.dt_to_ut(now_aware_dt)


@enforce_types
def test_dt_to_ut__main():
    # time = when unix time starts
    dt = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    ut = helpers.dt_to_ut(dt)
    assert ut == 0

    # time = one minute after when unix time starts
    dt = datetime.datetime(1970, 1, 1, 0, 1, 0, 0, tzinfo=timezone.utc)
    ut = helpers.dt_to_ut(dt)
    assert ut == 60


@enforce_types
def test_ut_to_dt__main():
    # time = when unix time starts
    ut = 0
    target_dt = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)

    dt = helpers.ut_to_dt(ut)
    assert dt.tzinfo == timezone.utc, "must be in UTC"
    assert dt == target_dt

    # time = one minute after when unix time starts
    ut = 60
    target_dt = datetime.datetime(1970, 1, 1, 0, 1, 0, 0, tzinfo=timezone.utc)

    dt = helpers.ut_to_dt(ut)
    assert dt.tzinfo == timezone.utc, "must be in UTC"
    assert dt == target_dt
