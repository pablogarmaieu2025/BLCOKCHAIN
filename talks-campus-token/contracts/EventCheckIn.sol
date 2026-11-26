// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {StudentPass} from "./StudentPass.sol";
import {CampusToken} from "./CampusToken.sol";

contract EventCheckIn is AccessControl {
    bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE");
    bytes32 public constant GATE_ROLE = keccak256("GATE_ROLE");
    uint256 public constant MAX_REWARD = 1000;
    uint256 public constant MAX_EVENT_CAPACITY = 1000;
    struct CampusEvent { uint256 reward; bool active; uint256 expiresAt; uint256 capacity; uint256 count; address organizer; }
    StudentPass public immutable pass;
    CampusToken public immutable token;
    mapping(bytes32 => CampusEvent) public events;
    mapping(bytes32 => mapping(address => bool)) public authorizedGate;
    mapping(bytes32 => mapping(bytes32 => bool)) private _checkedIn;
    mapping(bytes32 => uint256) private _reputation;
    event EventCreated(bytes32 indexed eventId, uint256 reward);
    event EventClosed(bytes32 indexed eventId);
    event GateAuthorized(bytes32 indexed eventId, address indexed gate, bool enabled);
    event CheckedIn(bytes32 indexed eventId, address indexed student, uint256 reward);
    error InvalidPass(address student);
    error EventNotActive(bytes32 eventId);
    error AlreadyCheckedIn(bytes32 eventId, address student);
    error EventExists();
    error InvalidEvent();
    error GateNotAuthorized();
    error NotEventOrganizer();
    error EventFull();

    constructor(address admin, StudentPass pass_, CampusToken token_) {
        pass = pass_; token = token_;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ORGANIZER_ROLE, admin);
    }
    function createEvent(bytes32 eventId, uint256 reward, uint256 expiresAt, uint256 capacity) external onlyRole(ORGANIZER_ROLE) {
        if (events[eventId].organizer != address(0)) revert EventExists();
        if (eventId == bytes32(0) || reward == 0 || reward > MAX_REWARD || expiresAt <= block.timestamp
            || capacity == 0 || capacity > MAX_EVENT_CAPACITY) revert InvalidEvent();
        events[eventId] = CampusEvent(reward, true, expiresAt, capacity, 0, msg.sender);
        emit EventCreated(eventId, reward);
    }
    function _requireOrganizer(bytes32 eventId) private view {
        address organizer = events[eventId].organizer;
        if (organizer == address(0) || (msg.sender != organizer && !hasRole(DEFAULT_ADMIN_ROLE, msg.sender))) revert NotEventOrganizer();
    }
    function authorizeGate(bytes32 eventId, address gate, bool enabled) external onlyRole(ORGANIZER_ROLE) {
        _requireOrganizer(eventId);
        if (enabled && !hasRole(GATE_ROLE, gate)) revert GateNotAuthorized();
        authorizedGate[eventId][gate] = enabled;
        emit GateAuthorized(eventId, gate, enabled);
    }
    function closeEvent(bytes32 eventId) external onlyRole(ORGANIZER_ROLE) {
        _requireOrganizer(eventId);
        events[eventId].active = false;
        emit EventClosed(eventId);
    }
    function checkedIn(bytes32 eventId, address student) public view returns (bool) {
        return _checkedIn[eventId][pass.studentKey(student)];
    }
    function reputation(address student) public view returns (uint256) {
        return _reputation[pass.studentKey(student)];
    }
    function checkIn(bytes32 eventId, address student) external onlyRole(GATE_ROLE) {
        if (!pass.isValid(student)) revert InvalidPass(student);
        CampusEvent storage e = events[eventId];
        if (!e.active || block.timestamp >= e.expiresAt) revert EventNotActive(eventId);
        if (!authorizedGate[eventId][msg.sender]) revert GateNotAuthorized();
        bytes32 key = pass.studentKey(student);
        if (_checkedIn[eventId][key]) revert AlreadyCheckedIn(eventId, student);
        if (e.count >= e.capacity) revert EventFull();
        _checkedIn[eventId][key] = true;
        _reputation[key] += 1;
        e.count += 1;
        token.mint(student, e.reward);
        emit CheckedIn(eventId, student, e.reward);
    }
}
