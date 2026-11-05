import numpy as np
import pytest

from veil import TeammateFaceMatcher, Veil, crypto, templates

RNG = np.random.default_rng(0)
SOFIA = templates.simulated_template(11)
KENJI = templates.simulated_template(29)


def test_same_face_is_granted():
    veil = Veil()
    wallet = veil.enroll("IE-1", SOFIA)
    assert veil.verify(wallet, templates.live_capture(SOFIA, rng=RNG), "gate").granted


def test_other_face_is_denied():
    veil = Veil()
    wallet = veil.enroll("IE-1", SOFIA)
    assert not veil.verify(wallet, templates.live_capture(KENJI, rng=RNG), "gate").granted


def test_protection_is_cancellable():
    a = templates.protect(SOFIA, b"salt-a")
    b = templates.protect(SOFIA, b"salt-b")
    assert not templates.is_match(a, b)


def test_two_scans_never_share_a_hash():
    # Why matching uses distance: the same face never gives the same bytes twice.
    s1, s2 = templates.live_capture(SOFIA, rng=RNG), templates.live_capture(SOFIA, rng=RNG)
    assert s1.tobytes() != s2.tobytes()
    assert templates.is_match(templates.protect(s1, b"x"), templates.protect(s2, b"x"))


def test_revoked_wallet_is_denied_and_new_one_works():
    veil = Veil()
    old = veil.enroll("IE-1", SOFIA)
    new, gap = veil.revoke_and_reissue(old, SOFIA)
    assert gap > templates.MATCH_THRESHOLD
    assert not veil.verify(old, templates.live_capture(SOFIA, rng=RNG), "gate").granted
    assert veil.verify(new, templates.live_capture(SOFIA, rng=RNG), "gate").granted


def test_tampered_wallet_is_denied():
    veil = Veil()
    wallet = veil.enroll("IE-1", SOFIA)
    wallet.salt = b"0" * 16  # attacker edits the wallet
    assert not veil.verify(wallet, templates.live_capture(SOFIA, rng=RNG), "gate").granted


def test_any_two_of_three_shares_rebuild_the_key():
    key = crypto.new_key()
    a, b, c = crypto.split_key(key)
    for pair in ([a, b], [a, c], [b, c]):
        assert crypto.combine_shares(pair) == key
    with pytest.raises(ValueError):  # one share alone reveals nothing
        crypto.combine_shares([a])


def test_ledger_detects_tampering():
    veil = Veil()
    veil.enroll("IE-1", SOFIA)
    assert veil.ledger.verify_chain()
    veil.ledger.blocks[1].fields["commitment"] = "f" * 64
    assert not veil.ledger.verify_chain()


def test_ledger_holds_no_names_or_faces():
    veil = Veil()
    veil.enroll("IE-24-0142", SOFIA)
    dump = " ".join(b.body() for b in veil.ledger.blocks)
    assert "IE-24-0142" not in dump
    assert str(round(float(SOFIA[0]), 6)) not in dump


def test_matcher_plugs_into_the_token_door():
    m = TeammateFaceMatcher()
    m.enroll("sara", SOFIA)
    m.enroll("marco", KENJI)
    assert m.identify(templates.live_capture(SOFIA, rng=RNG)) == "sara"
    assert m.identify(templates.simulated_template(999)) is None
    m.revoke("sara")
    assert m.identify(templates.live_capture(SOFIA, rng=RNG)) is None
