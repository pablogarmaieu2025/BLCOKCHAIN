// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title StudentPass
/// @notice One non-transferable pass per verified student wallet.
///         The pass stores NO personal data and NO biometric data:
///         only "this wallet belongs to a verified student".
///         Face matching happens off-chain, on the student's device.
contract StudentPass is ERC721, AccessControl {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");

    uint256 private _nextId = 1;
    mapping(address => uint256) public passOf;   // wallet => pass id (0 = none)
    mapping(uint256 => bool) public revoked;     // pass id => revoked?

    event PassIssued(address indexed student, uint256 indexed passId);
    event PassRevoked(address indexed student, uint256 indexed passId);

    error AlreadyHasPass(address student);
    error NoPass(address student);
    error Soulbound();

    constructor(address admin) ERC721("IE Student Pass", "PASS") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ISSUER_ROLE, admin);
    }

    /// @notice Issue a pass to a verified student (called by "IE", the issuer).
    function issue(address student) external onlyRole(ISSUER_ROLE) returns (uint256 passId) {
        if (passOf[student] != 0) revert AlreadyHasPass(student);
        passId = _nextId++;
        passOf[student] = passId;
        _safeMint(student, passId);
        emit PassIssued(student, passId);
    }

    /// @notice Revoke a pass (lost phone, left IE). Readers see it immediately.
    function revoke(address student) external onlyRole(ISSUER_ROLE) {
        uint256 passId = passOf[student];
        if (passId == 0) revert NoPass(student);
        revoked[passId] = true;
        emit PassRevoked(student, passId);
    }

    /// @notice What every door, event and app checks.
    function isValid(address student) public view returns (bool) {
        uint256 passId = passOf[student];
        return passId != 0 && !revoked[passId];
    }

    /// @dev Blocks every transfer: only minting (from = 0) is allowed.
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0)) revert Soulbound();
        return super._update(to, tokenId, auth);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
