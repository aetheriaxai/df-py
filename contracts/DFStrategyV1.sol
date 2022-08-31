// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
pragma solidity 0.8.12;

import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/utils/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/security/ReentrancyGuard.sol";
import "./interfaces/IDFRewards.sol";
import "./interfaces/IPool.sol";
import "./interfaces/IVeOCEAN.sol";



contract DFStrategyV1 is ReentrancyGuard {
    using SafeERC20 for IERC20;
    IDFRewards dfrewards;
    uint8 public id = 1;

    constructor(address _dfrewards) {
        dfrewards = IDFRewards(_dfrewards);
    }

    function claimMultiple(address _to, address[] calldata tokenAddresses)
        public
    {
        for (uint256 i = 0; i < tokenAddresses.length; i++) {
            dfrewards.claimFor(_to, tokenAddresses[i]);
        }
    }

    // Recipient claims for themselves
    function claim(address[] calldata tokenAddresses) external returns (bool) {
        claimMultiple(msg.sender, tokenAddresses);
        return true;
    }

    function claimables(address _to, address[] calldata tokenAddresses)
        external
        view
        returns (uint256[] memory result)
    {
        result = new uint256[](tokenAddresses.length);
        for (uint256 i = 0; i < tokenAddresses.length; i += 1) {
            result[i] = dfrewards.claimable(_to, tokenAddresses[i]);
        }
        return result;
    }

    function claimAndStake(
        address tokenAddress,
        uint256 totalAmount,
        address _veOCEAN
    ) public nonReentrant returns (bool) {
        require(
            dfrewards.claimable(msg.sender, tokenAddress) >= totalAmount,
            "Not enough rewards"
        );
        uint256 balanceBefore = IERC20(tokenAddress).balanceOf(address(this));
        uint256 claimed = dfrewards.claimForStrat(msg.sender, tokenAddress); // claim rewards for the strategy
        uint256 balanceAfter = IERC20(tokenAddress).balanceOf(address(this));
        require(balanceAfter - balanceBefore == claimed, "Not enough rewards");
        IERC20(tokenAddress).safeApprove(_veOCEAN, totalAmount);
        IVeOCEAN(_veOCEAN).deposit_for(msg.sender, totalAmount);

        if (claimed > totalAmount) {
            IERC20(tokenAddress).safeTransfer(
                msg.sender,
                claimed - totalAmount
            );
        }

        return true;
    }
}
