from fastapi.testclient import TestClient
from api.main import create_app

app = create_app()
client = TestClient(app)

def test_plan_chat_endpoint_fallback():
    plan_summary = {
        "building": {
            "intake": {
                "building_name": "Jefferson Market Library",
                "borough": "Manhattan",
            }
        },
        "outcome": {
            "label": "Scenario A cuts energy by 15%",
        },
        "scenarios": {
            "A": {"title": "Efficiency Only", "cost_usd": [50000, 75000]},
            "B": {"title": "Solar & Efficiency", "cost_usd": [200000, 250000]},
        },
        "referrals": [
            {"text": "Have an engineer verify usable roof area."}
        ]
    }
    
    # Test missing information question
    res = client.post(
        "/api/plans/chat",
        json={
            "plan_summary": plan_summary,
            "question": "What missing information do we need?",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "Jefferson Market Library" in data["reply"]
    assert "engineer" in data["reply"].lower()

    # Test cost reduction question
    res2 = client.post(
        "/api/plans/chat",
        json={
            "plan_summary": plan_summary,
            "question": "How can we reduce the upfront cost?",
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "reply" in data2
    assert "efficiency" in data2["reply"].lower()

def test_plan_chat_empty_question():
    res = client.post(
        "/api/plans/chat",
        json={
            "plan_summary": {},
            "question": "   ",
        },
    )
    assert res.status_code == 400
