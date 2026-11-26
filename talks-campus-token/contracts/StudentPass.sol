// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @notice Non-transferable student credential. Issuer verifies real-world uniqueness.
/// studentKey is a random opaque identifier, never a name, student number or biometric.
contract StudentPass is ERC721, AccessControl {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    uint256 private _nextId = 1;
    mapping(address => uint256) public passOf;
    mapping(uint256 => bool) public revoked;
    mapping(address => bytes32) public studentKey;
    mapping(bytes32 => address) public latestWallet;
    event PassIssued(address indexed student, uint256 indexed passId);
    event PassRevoked(address indexed student, uint256 indexed passId);
    event PassReplaced(address indexed oldWallet, address indexed newWallet);
    error AlreadyHasPass(address student);
    error NoPass(address student);
    error Soulbound();
    error InvalidStudentKey();
    error StudentAlreadyRegistered();
    error NotLatestWallet();

    constructor(address admin) ERC721("IE Student Pass", "PASS") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ISSUER_ROLE, admin);
    }

    function issue(address student, bytes32 key) external onlyRole(ISSUER_ROLE) returns (uint256) {
        if (passOf[student] != 0) revert AlreadyHasPass(student);
        if (key == bytes32(0)) revert InvalidStudentKey();
        if (latestWallet[key] != address(0)) revert StudentAlreadyRegistered();
        return _issue(student, key);
    }

    function _issue(address student, bytes32 key) private returns (uint256 id) {
        if (passOf[student] != 0) revert AlreadyHasPass(student);
        id = _nextId++;
        passOf[student] = id;
        studentKey[student] = key;
        latestWallet[key] = student;
        _mint(student, id);
        emit PassIssued(student, id);
    }

    function revoke(address student) public onlyRole(ISSUER_ROLE) {
        uint256 id = passOf[student];
        if (id == 0) revert NoPass(student);
        revoked[id] = true;
        emit PassRevoked(student, id);
    }

    /// @notice Recovery preserves the stable subject; old wallets never become valid again.
    function replace(address oldWallet, address newWallet) external onlyRole(ISSUER_ROLE) returns (uint256) {
        bytes32 key = studentKey[oldWallet];
        if (key == bytes32(0) || latestWallet[key] != oldWallet) revert NotLatestWallet();
        revoke(oldWallet);
        uint256 id = _issue(newWallet, key);
        emit PassReplaced(oldWallet, newWallet);
        return id;
    }

    function isValid(address student) public view returns (bool) {
        uint256 id = passOf[student];
        return id != 0 && !revoked[id] && latestWallet[studentKey[student]] == student;
    }

    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        if (_ownerOf(tokenId) != address(0)) revert Soulbound();
        return super._update(to, tokenId, auth);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
