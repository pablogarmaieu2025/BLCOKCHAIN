"""Tests for the contracts and the door. Run: python -m pytest -q"""
import pytest
from web3 import EthereumTesterProvider, Web3
from eth_tester.exceptions import TransactionFailed
from web3.exceptions import ContractCustomError, ContractLogicError

from gateway import CampusChain, DemoFaceMatcher, Door, Roles, StudentRegistry

# The local test chain raises TransactionFailed; a real node raises the web3 errors.
REVERT_ERRORS = (TransactionFailed, ContractCustomError, ContractLogicError)


def revert_data(exc) -> str:
    """Hex of every revert payload found on the exception and the errors it wraps."""
    found = []
    while exc is not None:
        for candidate in (getattr(exc, "data", None), *getattr(exc, "args", ())):
            if isinstance(candidate, (bytes, bytearray)):
                found.append(candidate.hex())
            elif isinstance(candidate, str):
                found.append(candidate)
        exc = exc.__cause__ or exc.__context__
    return " ".join(found)


def selector(signature: str) -> str:
    return Web3.keccak(text=signature)[:4].hex()


def reverts(signature: str):
    """Asserts the call reverts with this custom error, e.g. 'Soulbound()'."""
    class _Ctx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            assert exc_type is not None, f"expected revert {signature}"
            assert issubclass(exc_type, REVERT_ERRORS), exc
            assert selector(signature).removeprefix("0x") in revert_data(exc), (signature, exc)
            return True
    return _Ctx()


@pytest.fixture
def env():
    w3 = Web3(EthereumTesterProvider())
    ie, gate, a, b, outsider = w3.eth.accounts[:5]
    chain = CampusChain.deploy(w3, Roles(admin=ie, gate=gate))
    chain.issue_pass(a)
    chain.issue_pass(b)
    return w3, chain, ie, gate, a, b, outsider


# ---------- StudentPass ----------
def test_pass_is_valid_after_issue(env):
    _, chain, *_, a, b, outsider = env
    assert chain.is_valid(a) and chain.is_valid(b)
    assert not chain.is_valid(outsider)


def test_one_pass_per_wallet(env):
    _, chain, *_, a, _b, _o = env
    with reverts("AlreadyHasPass(address)"):
        chain.issue_pass(a)


def test_pass_cannot_be_transferred(env):
    _, chain, *_, a, b, _o = env
    pass_id = chain.pass_.functions.passOf(a).call()
    with reverts("Soulbound()"):
        chain.pass_.functions.transferFrom(a, b, pass_id).transact({"from": a})


def test_only_issuer_can_issue(env):
    _, chain, *_, a, _b, outsider = env
    with pytest.raises(REVERT_ERRORS):
        chain.pass_.functions.issue(outsider).transact({"from": a})


def test_revoked_pass_is_invalid(env):
    _, chain, *_, a, _b, _o = env
    chain.revoke_pass(a)
    assert not chain.is_valid(a)


# ---------- EventCheckIn + CampusToken ----------
def test_check_in_pays_reward_once(env):
    _, chain, *_, a, _b, _o = env
    chain.create_event("debate", 100)
    chain.check_in("debate", a)
    assert chain.balance(a) == 100 and chain.reputation(a) == 1
    with reverts("AlreadyCheckedIn(bytes32,address)"):
        chain.check_in("debate", a)


def test_check_in_requires_valid_pass(env):
    _, chain, *_, _a, _b, outsider = env
    chain.create_event("debate", 100)
    with reverts("InvalidPass(address)"):
        chain.check_in("debate", outsider)


def test_only_gate_can_check_in(env):
    _, chain, _ie, _gate, a, _b, _o = env
    chain.create_event("debate", 100)
    with pytest.raises(REVERT_ERRORS):
        chain.checkin.functions.checkIn(Web3.keccak(text="debate"), a).transact({"from": a})


def test_closed_event_pays_nothing(env):
    _, chain, *_, a, _b, _o = env
    chain.create_event("debate", 100)
    chain._tx(chain.checkin.functions.closeEvent(Web3.keccak(text="debate")), chain.roles.admin)
    with reverts("EventNotActive(bytes32)"):
        chain.check_in("debate", a)


def test_tokens_only_move_between_students(env):
    _, chain, *_, a, b, outsider = env
    chain.create_event("debate", 100)
    chain.check_in("debate", a)
    chain.send(a, b, 40)
    assert chain.balance(b) == 40
    with reverts("NotAStudent(address)"):
        chain.send(a, outsider, 10)


def test_nobody_else_can_mint(env):
    _, chain, ie, *_ = env
    with pytest.raises(REVERT_ERRORS):
        chain.token.functions.mint(ie, 1000).transact({"from": ie})


# ---------- Perks ----------
def test_unlock_burns_tokens_and_counts_supply(env):
    _, chain, *_, a, _b, _o = env
    chain.create_event("debate", 300)
    chain.check_in("debate", a)
    chain.create_perk("early access", price=200, supply=50)
    chain.unlock_perk("early access", a)
    assert chain.has_perk("early access", a)
    assert chain.balance(a) == 100
    assert chain.total_supply() == 100
    assert chain.perk_remaining("early access") == 49


def test_unlock_fails_without_enough_tokens(env):
    _, chain, *_, a, _b, _o = env
    chain.create_perk("early access", price=200, supply=50)
    with reverts("ERC20InsufficientBalance(address,uint256,uint256)"):
        chain.unlock_perk("early access", a)
    assert chain.perk_remaining("early access") == 50  # failed unlock changes nothing


def test_perk_sells_out(env):
    _, chain, *_, a, b, _o = env
    chain.create_event("debate", 100)
    chain.check_in("debate", a)
    chain.check_in("debate", b)
    chain.create_perk("dinner seat", price=50, supply=1)
    chain.unlock_perk("dinner seat", a)
    with reverts("SoldOut(bytes32)"):
        chain.unlock_perk("dinner seat", b)


def test_perk_once_per_student(env):
    _, chain, *_, a, _b, _o = env
    chain.create_event("debate", 300)
    chain.check_in("debate", a)
    chain.create_perk("early access", price=100, supply=50)
    chain.unlock_perk("early access", a)
    with reverts("AlreadyOwned(bytes32,address)"):
        chain.unlock_perk("early access", a)


# ---------- Door ----------
def test_door_flow(env):
    _, chain, *_, a, _b, _o = env
    matcher, registry = DemoFaceMatcher(), StudentRegistry()
    matcher.enroll("sara", "sara-enrol")
    registry.register("sara", a)
    door = Door(chain, matcher, registry)
    chain.create_event("debate", 100)

    assert not door.scan("stranger-1").granted
    assert door.scan("sara-1").granted
    first = door.scan("sara-2", event="debate")
    second = door.scan("sara-3", event="debate")
    assert first.tokens_earned == 100 and second.tokens_earned == 0

    chain.revoke_pass(a)
    assert door.scan("sara-4").reason == "pass missing or revoked"
