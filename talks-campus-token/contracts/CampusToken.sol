// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {StudentPass} from "./StudentPass.sol";

/// @title CampusToken
/// @notice Earned by taking part in campus life, spent on perks.
///         Closed network: only wallets with a valid StudentPass can receive tokens.
///         Never sold, no euro value. Whole units only (decimals = 0).
contract CampusToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");   // EventCheckIn contract
    bytes32 public constant SPENDER_ROLE = keccak256("SPENDER_ROLE"); // Perks contract

    StudentPass public immutable pass;

    error NotAStudent(address account);

    constructor(address admin, StudentPass pass_) ERC20("talks. Campus Token", "TALK") {
        pass = pass_;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    function decimals() public pure override returns (uint8) {
        return 0;
    }

    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }

    /// @notice Burns tokens when a student spends them on a perk.
    function spend(address from, uint256 amount) external onlyRole(SPENDER_ROLE) {
        _burn(from, amount);
    }

    /// @dev Every mint and transfer must land in a verified student's wallet.
    function _update(address from, address to, uint256 value) internal override {
        if (to != address(0) && !pass.isValid(to)) revert NotAStudent(to);
        super._update(from, to, value);
    }
}
