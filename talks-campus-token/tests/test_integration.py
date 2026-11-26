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
