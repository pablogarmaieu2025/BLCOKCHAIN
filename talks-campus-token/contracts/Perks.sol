// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {StudentPass} from "./StudentPass.sol";
import {CampusToken} from "./CampusToken.sol";

contract Perks is AccessControl {
    bytes32 public constant PERK_MANAGER_ROLE = keccak256("PERK_MANAGER_ROLE");
    struct Perk { uint256 price; uint256 supply; uint256 claimed; bool active; address manager; }
    StudentPass public immutable pass;
    CampusToken public immutable token;
    mapping(bytes32 => Perk) public perks;
    mapping(bytes32 => mapping(bytes32 => bool)) private _hasPerk;
    event PerkCreated(bytes32 indexed perkId, uint256 price, uint256 supply);
    event PerkUnlocked(bytes32 indexed perkId, address indexed student, uint256 price);
    event PerkClosed(bytes32 indexed perkId);
    error InvalidPass(address student);
    error PerkNotActive(bytes32 perkId);
    error SoldOut(bytes32 perkId);
    error AlreadyOwned(bytes32 perkId, address student);
    error PerkExists();
    error InvalidPerk();
    error NotPerkManager();
    constructor(address admin, StudentPass pass_, CampusToken token_) {
        pass = pass_; token = token_;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(PERK_MANAGER_ROLE, admin);
    }
    function createPerk(bytes32 perkId, uint256 price, uint256 supply) external onlyRole(PERK_MANAGER_ROLE) {
        if (perks[perkId].manager != address(0)) revert PerkExists();
        if (perkId == bytes32(0) || price == 0 || supply == 0) revert InvalidPerk();
        perks[perkId] = Perk(price, supply, 0, true, msg.sender);
        emit PerkCreated(perkId, price, supply);
    }
    function closePerk(bytes32 perkId) external onlyRole(PERK_MANAGER_ROLE) {
        address manager = perks[perkId].manager;
        if (manager == address(0) || (msg.sender != manager && !hasRole(DEFAULT_ADMIN_ROLE, msg.sender))) revert NotPerkManager();
        perks[perkId].active = false;
        emit PerkClosed(perkId);
    }
    function hasPerk(bytes32 perkId, address student) public view returns (bool) {
        return _hasPerk[perkId][pass.studentKey(student)];
    }
    function unlock(bytes32 perkId) external {
        if (!pass.isValid(msg.sender)) revert InvalidPass(msg.sender);
        Perk storage p = perks[perkId];
        if (!p.active) revert PerkNotActive(perkId);
        if (p.claimed >= p.supply) revert SoldOut(perkId);
        bytes32 key = pass.studentKey(msg.sender);
        if (_hasPerk[perkId][key]) revert AlreadyOwned(perkId, msg.sender);
        p.claimed += 1;
        _hasPerk[perkId][key] = true;
        token.spend(msg.sender, p.price);
        emit PerkUnlocked(perkId, msg.sender, p.price);
    }
    function remaining(bytes32 perkId) external view returns (uint256) {
        Perk memory p = perks[perkId];
        return p.supply - p.claimed;
    }
}
