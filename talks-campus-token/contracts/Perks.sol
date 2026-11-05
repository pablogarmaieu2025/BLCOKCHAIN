// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {StudentPass} from "./StudentPass.sol";
import {CampusToken} from "./CampusToken.sol";

/// @title Perks
/// @notice Scarce things students spend tokens on, e.g. a 24-hour early
///         ticket window for a sold-out talks. event. Spent tokens are burned.
///         Supply is public, so scarcity is provable.
contract Perks is AccessControl {
    bytes32 public constant PERK_MANAGER_ROLE = keccak256("PERK_MANAGER_ROLE");

    struct Perk {
        uint256 price;    // in tokens
        uint256 supply;   // total available
        uint256 claimed;  // already unlocked
        bool active;
    }

    StudentPass public immutable pass;
    CampusToken public immutable token;

    mapping(bytes32 => Perk) public perks;
    mapping(bytes32 => mapping(address => bool)) public hasPerk;

    event PerkCreated(bytes32 indexed perkId, uint256 price, uint256 supply);
    event PerkUnlocked(bytes32 indexed perkId, address indexed student, uint256 price);

    error InvalidPass(address student);
    error PerkNotActive(bytes32 perkId);
    error SoldOut(bytes32 perkId);
    error AlreadyOwned(bytes32 perkId, address student);

    constructor(address admin, StudentPass pass_, CampusToken token_) {
        pass = pass_;
        token = token_;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(PERK_MANAGER_ROLE, admin);
    }

    function createPerk(bytes32 perkId, uint256 price, uint256 supply) external onlyRole(PERK_MANAGER_ROLE) {
        perks[perkId] = Perk({price: price, supply: supply, claimed: 0, active: true});
        emit PerkCreated(perkId, price, supply);
    }

    /// @notice A student spends tokens on a perk. Reverts if the balance is too low.
    function unlock(bytes32 perkId) external {
        if (!pass.isValid(msg.sender)) revert InvalidPass(msg.sender);
        Perk storage p = perks[perkId];
        if (!p.active) revert PerkNotActive(perkId);
        if (p.claimed >= p.supply) revert SoldOut(perkId);
        if (hasPerk[perkId][msg.sender]) revert AlreadyOwned(perkId, msg.sender);

        p.claimed += 1;
        hasPerk[perkId][msg.sender] = true;
        token.spend(msg.sender, p.price); // burns; reverts on insufficient balance
        emit PerkUnlocked(perkId, msg.sender, p.price);
    }

    function remaining(bytes32 perkId) external view returns (uint256) {
        Perk memory p = perks[perkId];
        return p.supply - p.claimed;
    }
}
