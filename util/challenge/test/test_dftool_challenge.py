import os

from enforce_typing import enforce_types
import pytest
from typing import Optional

from util.challenge import judge
from util import csvs


@enforce_types
def test1(tmp_path):
    _test(tmp_path, DEADLINE=None, RETRIES=None)


@enforce_types
def test2(tmp_path):
    _test(tmp_path, DEADLINE="None", RETRIES=None)


@enforce_types
def test3(tmp_path):
    _test(tmp_path, DEADLINE="None", RETRIES=2)


@enforce_types
def test4(tmp_path):
    _test(tmp_path, DEADLINE="2023-05-03_23:59", RETRIES=None)


@enforce_types
def test5(tmp_path):
    _test(tmp_path, DEADLINE="2023-05-03_23:59", RETRIES=2)


@enforce_types
def _test(tmp_path, DEADLINE: Optional[str], RETRIES: Optional[int]):
    # build base cmd
    base_dir = str(tmp_path)
    CSV_DIR = os.path.join(base_dir, judge.DFTOOL_TEST_FAKE_CSVDIR)
    os.mkdir(CSV_DIR)
    cmd = f"./dftool challenge_data {CSV_DIR}"

    # tack on 1 or 2 args to cmd as needed
    if DEADLINE is None and RETRIES is None:
        pass
    elif DEADLINE is None and RETRIES is not None:
        assert ValueError("must specify DEADLINE if RETRIES is not None")
    elif DEADLINE is not None and RETRIES is None:
        cmd += f" {DEADLINE}"
    elif DEADLINE is not None and RETRIES is not None:
        cmd += f" {DEADLINE} {RETRIES}"
    else:
        raise AssertionError("shouldn't end up here")

    # main call
    print(f"CMD: {cmd}")
    os.system(cmd)

    # targets
    (
        target_from_addrs,
        target_nft_addrs,
        target_nmses,
    ) = judge.DFTOOL_TEST_FAKE_CHALLENGE_DATA

    # test result
    (from_addrs, nft_addrs, nmses) = csvs.loadChallengeDataCsv(CSV_DIR)

    assert len(from_addrs) == len(nft_addrs) == len(nmses)
    assert sorted(nmses) == nmses

    assert from_addrs == target_from_addrs
    assert nft_addrs == target_nft_addrs
    assert nmses == target_nmses


@enforce_types
def test_challenge_help():
    cmd = f"./dftool challenge_data"
    os.system(cmd)
