// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {StudentPass} from "./StudentPass.sol";
import {CampusToken} from "./CampusToken.sol";

/// @title EventCheckIn
/// @notice Doors and event scanners ("gates") check students in.
///         Each check-in pays the event's reward once per student and
///         adds to a reputation count that cannot be bought or transferred.
///         The chain records THAT a wallet checked in, never a face or a name.
contract EventCheckIn is AccessControl {
    bytes32 public constant ORGANIZER_ROLE = keccak256("ORGANIZER_ROLE"); // student gov, talks.
    bytes32 public constant GATE_ROLE = keccak256("GATE_ROLE");           // door / scanner devices

    struct CampusEvent {
        uint256 reward;
        bool active;
    }

    StudentPass public immutable pass;
    CampusToken public immutable token;

    mapping(bytes32 => CampusEvent) public events;
    mapping(bytes32 => mapping(address => bool)) public checkedIn;
    mapping(address => uint256) public reputation; // number of check-ins

    event EventCreated(bytes32 indexed eventId, uint256 reward);
    event EventClosed(bytes32 indexed eventId);
    event CheckedIn(bytes32 indexed eventId, address indexed student, uint256 reward);

    error InvalidPass(address student);
    error EventNotActive(bytes32 eventId);
    error AlreadyCheckedIn(bytes32 eventId, address student);

    constructor(address admin, StudentPass pass_, CampusToken token_) {
        pass = pass_;
        token = token_;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ORGANIZER_ROLE, admin);
    }

    function createEvent(bytes32 eventId, uint256 reward) external onlyRole(ORGANIZER_ROLE) {
        events[eventId] = CampusEvent({reward: reward, active: true});
        emit EventCreated(eventId, reward);
    }

    function closeEvent(bytes32 eventId) external onlyRole(ORGANIZER_ROLE) {
        events[eventId].active = false;
        emit EventClosed(eventId);
    }

    /// @notice Called by a gate after the student's identity was confirmed off-chain.
    function checkIn(bytes32 eventId, address student) external onlyRole(GATE_ROLE) {
        if (!pass.isValid(student)) revert InvalidPass(student);
        CampusEvent memory e = events[eventId];
        if (!e.active) revert EventNotActive(eventId);
        if (checkedIn[eventId][student]) revert AlreadyCheckedIn(eventId, student);

        checkedIn[eventId][student] = true;
        reputation[student] += 1;
        token.mint(student, e.reward);
        emit CheckedIn(eventId, student, e.reward);
    }
}
