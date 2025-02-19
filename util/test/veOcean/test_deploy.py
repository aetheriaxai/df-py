import brownie
from enforce_typing import enforce_types
from util import networkutil, oceanutil

from util.constants import BROWNIE_PROJECT as B

accounts = None


@enforce_types
def test_deploy_ve():
    """Test deploy veOCEAN contract."""
    OCEAN = oceanutil.OCEANtoken()

    veOCEAN = B.veOcean.deploy(
        OCEAN.address, "veOCEAN", "veOCEAN", "0.1.0", {"from": accounts[0]}
    )

    assert veOCEAN.admin() == accounts[0].address


@enforce_types
def setup_function():
    networkutil.connectDev()
    oceanutil.recordDevDeployedContracts()
    global accounts
    accounts = brownie.network.accounts


@enforce_types
def teardown_function():
    networkutil.disconnect()
