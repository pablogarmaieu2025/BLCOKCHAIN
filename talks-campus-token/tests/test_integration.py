"""Actual Veil adapter + Door + deployed local EVM contracts, synthetic inputs only."""
import pytest
from gateway.demo_campus import DemoCampus

@pytest.fixture
def campus():
    return DemoCampus()

def test_protected_match_mints_once(campus):
    r = campus.scan("sara", "SG debate")
    assert r.granted and r.tokens_earned == 100 and r.tx_hash
    assert campus.scan("sara", "SG debate").tokens_earned == 0
    assert campus.chain.balance(campus.sara) == 100
    assert campus.chain.reputation(campus.sara) == 1

def test_unknown_and_both_revocation_layers(campus):
    assert not campus.scan("unknown", "SG debate").granted
    campus.matcher.revoke("sara")
    assert not campus.scan("sara", "SG debate").granted
    campus.chain.revoke_pass(campus.marco)
    assert not campus.scan("marco", "SG debate").granted
    assert campus.chain.total_supply() == 0

def test_end_to_end_redemption(campus):
    for event in campus.events:
        assert campus.scan("sara", event).tokens_earned == 100
    campus.chain.unlock_perk(campus.perk, campus.sara)
    assert campus.chain.balance(campus.sara) == 100
    assert campus.chain.total_supply() == 100
    assert campus.chain.perk_remaining(campus.perk) == 49

def test_closed_event_fails_without_minting(campus):
    from gateway import to_id
    chain = campus.chain
    chain._tx(chain.checkin.functions.closeEvent(to_id("SG debate")), campus.admin)
    assert not campus.scan("sara", "SG debate").granted
    assert chain.total_supply() == 0

def test_duplicate_registrar_enrollment(campus):
    with pytest.raises(ValueError):
        campus.registry.register("sara", campus.outsider)
    with pytest.raises(ValueError):
        campus.registry.register("different", campus.sara)


# Adapted from the teammate's independent integration suite (25 Nov 2026).
def test_right_person_gets_the_tokens(campus):
    result = campus.scan("marco", "SG debate")
    assert result.granted and result.student_id == "marco" and result.wallet == campus.marco
    assert campus.chain.balance(campus.marco) == 100
    assert campus.chain.balance(campus.sara) == 0
    assert campus.chain.reputation(campus.marco) == 1
    assert campus.chain.reputation(campus.sara) == 0

def test_checkin_calldata_contains_only_expected_public_fields(campus):
    """Specific ABI and literal-data regression, not a general anonymity proof."""
    from gateway import to_id
    from web3 import Web3
    from veil import templates
    chain = campus.chain
    credential = campus.matcher._wallets["sara"]
    result = campus.scan("sara", "SG debate")
    assert result.granted and result.tx_hash
    tx = chain.w3.eth.get_transaction(Web3.to_hex(bytes.fromhex(result.tx_hash.removeprefix("0x"))))
    assert tx["from"] == campus.gate and tx["to"] == chain.checkin.address
    payload = tx.get("input", tx.get("data"))
    raw = bytes(payload) if not isinstance(payload, str) else bytes.fromhex(payload.removeprefix("0x"))
    fn, args = chain.checkin.decode_function_input(Web3.to_hex(raw))
    assert fn.fn_name == "checkIn"
    assert args == {"eventId": to_id("SG debate"), "student": campus.sara}
    assert len(raw) == 4 + 32 + 32
    assert credential.did.encode() not in raw
    assert credential.salt not in raw
    assert credential.ciphertext.data not in raw
    assert campus.raw["sara"].tobytes() not in raw
    assert templates.protect(campus.raw["sara"], credential.salt).tobytes() not in raw
    # Enrollment exposes the random subject key, NOT a biometric credential.
    assert chain.pass_.functions.studentKey(campus.sara).call() == campus.registry.record_of("sara").key
    assert chain.pass_.functions.studentKey(campus.sara).call() != Web3.keccak(text=credential.did)
