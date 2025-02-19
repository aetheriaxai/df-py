from enforce_typing import enforce_types
import pytest

from util import cleancase


@enforce_types
def test_allocations():
    allocs = {
        1: {
            "0xpOolA": {"0xLp1": 1.0, "0xLP2": 1.0},
            "0xPOOLB": {"0xLP3": 1.0},
            "0xPOoLC": {"0xlP4": 1.0},
        },
        2: {"0xPOOLD": {"0xLP5": 1.0}},
    }
    target_allocs = {
        1: {
            "0xpoola": {"0xlp1": 1.0, "0xlp2": 1.0},
            "0xpoolb": {"0xlp3": 1.0},
            "0xpoolc": {"0xlp4": 1.0},
        },
        2: {"0xpoold": {"0xlp5": 1.0}},
    }

    with pytest.raises(AssertionError):
        cleancase.assertAllocations(allocs)

    mod_allocs = cleancase.modAllocations(allocs)
    cleancase.assertAllocations(mod_allocs)
    assert mod_allocs == target_allocs


@enforce_types
def test_allocations_fail():
    allocations = {
        1: {
            "0xpoola": {"0xlp1": 0.5},
            "0xpoolb": {"0xlp1": 0.51},
        },
    }

    with pytest.raises(AssertionError) as excinfo:
        cleancase.assertAllocations(allocations)
    assert str(excinfo.value) == "LP 0xlp1 has 1.01% allocation, > 1.0%"


@enforce_types
def test_stakes():
    stakes = {
        1: {
            "0xpOolA": {"0xLp1": 10.0, "0xLP2": 10.0},
            "0xPOOLB": {"0xLP3": 10.0},
            "0xPOoLC": {"0xlP4": 10.0},
        },
        2: {"0xPOOLD": {"0xLP5": 10.0}},
    }
    target_stakes = {
        1: {
            "0xpoola": {"0xlp1": 10.0, "0xlp2": 10.0},
            "0xpoolb": {"0xlp3": 10.0},
            "0xpoolc": {"0xlp4": 10.0},
        },
        2: {"0xpoold": {"0xlp5": 10.0}},
    }

    with pytest.raises(AssertionError):
        cleancase.assertStakes(stakes)

    mod_stakes = cleancase.modStakes(stakes)
    cleancase.assertStakes(mod_stakes)
    assert mod_stakes == target_stakes


@enforce_types
def test_vebals1_fixcase():
    vebals = {"0xLp1": 10.1, "0xLP2": 20.2}
    target_vebals = {"0xlp1": 10.1, "0xlp2": 20.2}

    with pytest.raises(AssertionError):
        cleancase.assertVebals(vebals)

    mod_vebals = cleancase.modVebals(vebals)
    cleancase.assertVebals(mod_vebals)
    assert mod_vebals == target_vebals


@enforce_types
def test_vebals2_missing0x():
    vebals = {"lp1": 10.1}

    with pytest.raises(AssertionError):
        cleancase.assertVebals(vebals)


@enforce_types
def test_nftvols():
    poolvols = {
        1: {"0xoCeAn": {"0xpOolA": 1.0, "0xPOOLB": 2.0}, "0xH2o": {"0xPOoLC": 3.0}},
        2: {"0xocean": {"0xPOOLD": 4.0}},
    }

    target_poolvols = {
        1: {"0xocean": {"0xpoola": 1.0, "0xpoolb": 2.0}, "0xh2o": {"0xpoolc": 3.0}},
        2: {"0xocean": {"0xpoold": 4.0}},
    }

    with pytest.raises(AssertionError):
        cleancase.assertNFTvols(poolvols)

    mod_poolvols = cleancase.modNFTvols(poolvols)
    cleancase.assertNFTvols(mod_poolvols)
    assert mod_poolvols == target_poolvols


@enforce_types
def test_symbols():
    symbols = {
        1: {"0xoCeAn": "oCeAn", "0xh2o": "H2o"},
        2: {"0xoceaN": "mOCEan", "0xh2O": "h2O"},
    }
    target_symbols = {
        1: {"0xocean": "OCEAN", "0xh2o": "H2O"},
        2: {"0xocean": "MOCEAN", "0xh2o": "H2O"},
    }

    with pytest.raises(AssertionError):
        cleancase.assertSymbols(symbols)

    mod_symbols = cleancase.modSymbols(symbols)
    cleancase.assertSymbols(mod_symbols)
    assert mod_symbols == target_symbols


@enforce_types
def test_rates_main():
    rates = {"oCeAn": 0.25, "h2o": 1.61}
    target_rates = {"OCEAN": 0.25, "H2O": 1.61}

    with pytest.raises(AssertionError):
        cleancase.assertRates(rates)

    mod_rates = cleancase.modRates(rates)
    cleancase.assertRates(mod_rates)
    assert mod_rates == target_rates


@enforce_types
def test_rates_0x():
    rates = {"0xOCEAN": 0.1}
    with pytest.raises(AssertionError):
        cleancase.assertRates(rates)


@enforce_types
def test_owners():
    owners = {
        1: {"0xNFt1": "0xLp1", "0xNfT2": "0xlP2"},
        2: {"0xnFT2": "0xlP2n", "0xnfT3": "0xLP3"},
    }
    target_owners = {
        1: {"0xnft1": "0xlp1", "0xnft2": "0xlp2"},
        2: {"0xnft2": "0xlp2n", "0xnft3": "0xlp3"},
    }

    with pytest.raises(AssertionError):
        cleancase.assertOwners(owners)

    mod_owners = cleancase.modOwners(owners)
    cleancase.assertOwners(mod_owners)
    assert mod_owners == target_owners
