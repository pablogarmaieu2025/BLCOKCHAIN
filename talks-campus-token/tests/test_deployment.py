"""Signed local rehearsal; never connects to a public RPC."""
import json
from scripts.deploy import run

def test_signed_deployment_and_smoke(tmp_path):
    out = tmp_path / "local.json"
    result = run(local=True, smoke=True, out=out)
    assert json.loads(out.read_text()) == result
    assert result["ephemeral"] and result["seeded"] and result["smoke_passed"]
    assert result["admin"] != result["gate"] != result["smoke"]["student"]
    assert result["smoke"]["outstanding"] == 0
    assert len(result["contracts"]) == 4
    assert all(c["deployment"]["status"] == 1 and c["explorer"] is None for c in result["contracts"].values())
    assert all(r["status"] == 1 for r in result["transactions"])
