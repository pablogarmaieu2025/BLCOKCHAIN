// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {StudentPass} from "./StudentPass.sol";

/// @notice Closed-loop reward units. Transfers require two active students.
/// The illustrative lifetime issuance ceiling is not a euro backing or market price.
contract CampusToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant SPENDER_ROLE = keccak256("SPENDER_ROLE");
    bytes32 public constant RECOVERY_ROLE = keccak256("RECOVERY_ROLE");
    uint256 public constant LIFETIME_ISSUANCE_CAP = 1_000_000;
    uint256 public lifetimeMinted;
    StudentPass public immutable pass;
    error NotAStudent(address account);
    error IssuanceCapExceeded();
    error InvalidRecovery();
    event BalanceRecovered(address indexed oldWallet, address indexed newWallet, uint256 amount);

    constructor(address admin, StudentPass pass_) ERC20("talks. Campus Token", "TALK") {
        pass = pass_;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(RECOVERY_ROLE, admin);
    }
    function decimals() public pure override returns (uint8) { return 0; }

    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        if (amount > LIFETIME_ISSUANCE_CAP - lifetimeMinted) revert IssuanceCapExceeded();
        lifetimeMinted += amount;
        _mint(to, amount);
    }
    function spend(address from, uint256 amount) external onlyRole(SPENDER_ROLE) {
        if (!pass.isValid(from)) revert NotAStudent(from);
        _burn(from, amount);
    }

    /// @notice Authorized recovery only between wallets of the same verified subject.
    /// No mint or burn; historical revoked accounts cannot transfer normally.
    function recoverBalance(address oldWallet, address newWallet) external onlyRole(RECOVERY_ROLE) {
        bytes32 key = pass.studentKey(oldWallet);
        if (key == bytes32(0) || pass.isValid(oldWallet) || !pass.isValid(newWallet)
            || key != pass.studentKey(newWallet)) revert InvalidRecovery();
        uint256 amount = balanceOf(oldWallet);
        super._update(oldWallet, newWallet, amount);
        emit BalanceRecovered(oldWallet, newWallet, amount);
    }
    function _update(address from, address to, uint256 value) internal override {
        if (from != address(0) && !pass.isValid(from)) revert NotAStudent(from);
        if (to != address(0) && !pass.isValid(to)) revert NotAStudent(to);
        super._update(from, to, value);
    }
}
