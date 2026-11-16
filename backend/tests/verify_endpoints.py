import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def log(msg):
    print(msg, flush=True)

def test_live_api():
    log(f"Testing live Flask API at {BASE_URL}...")

    # 1. Health
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200, f"Health failed: {r.text}"
    log("[OK] GET /api/health passed")

    # 2. Dashboard stats
    r = requests.get(f"{BASE_URL}/api/dashboard/stats")
    assert r.status_code == 200
    d = r.json()
    assert d["success"] is True
    log(f"[OK] GET /api/dashboard/stats passed ({d['data']['students_count']} students, {d['data']['facts_count']} facts)")

    # 3. Students
    r = requests.get(f"{BASE_URL}/api/students")
    assert r.status_code == 200
    students = r.json()["data"]
    assert len(students) >= 5
    first_id = students[0]["id"]
    r_detail = requests.get(f"{BASE_URL}/api/students/{first_id}")
    assert r_detail.status_code == 200
    log(f"[OK] GET /api/students & detail passed (found {len(students)} students)")

    # 4. Professors
    r = requests.get(f"{BASE_URL}/api/professors")
    assert r.status_code == 200
    profs = r.json()["data"]
    assert len(profs) >= 3
    log(f"[OK] GET /api/professors passed (found {len(profs)} professors)")

    # 5. Courses
    r = requests.get(f"{BASE_URL}/api/courses")
    assert r.status_code == 200
    courses = r.json()["data"]
    assert len(courses) >= 5
    log(f"[OK] GET /api/courses passed (found {len(courses)} courses)")

    # 6. Departments
    r = requests.get(f"{BASE_URL}/api/departments")
    assert r.status_code == 200
    depts = r.json()["data"]
    assert len(depts) >= 3
    log(f"[OK] GET /api/departments passed (found {len(depts)} departments)")

    # 7. Facts
    r = requests.get(f"{BASE_URL}/api/facts?page=1&page_size=10")
    assert r.status_code == 200
    facts_data = r.json()["data"]
    assert facts_data["total"] > 0
    log(f"[OK] GET /api/facts passed (total facts: {facts_data['total']})")

    # 8. Rules
    r = requests.get(f"{BASE_URL}/api/rules")
    assert r.status_code == 200
    rules = r.json()["data"]
    assert len(rules) == 15
    log(f"[OK] GET /api/rules passed (15 predefined rules active)")

    # 9. Test rule dry-run
    r = requests.post(f"{BASE_URL}/api/rules/test", json={"rule_text": "Enrolled(x,y) -> Studies(x,y)"})
    assert r.status_code == 200
    log("[OK] POST /api/rules/test dry-run passed")

    # 10. Backward inference
    r = requests.post(f"{BASE_URL}/api/inference/backward", json={"goal": "Studies(Ravi, AI)"})
    assert r.status_code == 200
    assert r.json()["data"]["truth_value"] == "TRUE"
    log("[OK] POST /api/inference/backward passed (Studies(Ravi, AI) -> TRUE)")

    # 11. Forward inference
    r = requests.post(f"{BASE_URL}/api/inference/forward")
    assert r.status_code == 200
    inf_res = r.json()["data"]
    log(f"[OK] POST /api/inference/forward passed ({inf_res['new_facts_count']} facts derived in {inf_res['iterations']} iterations)")

    # 12. Natural Language Query
    queries_to_test = [
        "Who teaches AI?",
        "Which students study AI?",
        "Is Ravi enrolled in AI?",
        "Who is the head of CSE?",
        "What are the prerequisites of ML?",
        "Who is Ravi's professor?"
    ]
    for q in queries_to_test:
        r = requests.post(f"{BASE_URL}/api/query", json={"question": q})
        assert r.status_code == 200, f"Query '{q}' failed: {r.text}"
        ans = r.json()["data"]
        safe_lq = ans['logical_query'].replace('∧', '&')
        log(f"[OK] Query '{q}' -> {safe_lq} => {ans['answers']} ({ans['truth_value']})")

    # 13. Knowledge Graph
    r = requests.get(f"{BASE_URL}/api/knowledge-graph")
    assert r.status_code == 200
    g = r.json()["data"]
    assert g["total_nodes"] > 0
    log(f"[OK] GET /api/knowledge-graph passed ({g['total_nodes']} nodes, {g['total_edges']} edges)")

    # 14. Reports
    r_csv = requests.get(f"{BASE_URL}/api/reports/export?type=students&format=csv")
    assert r_csv.status_code == 200
    r_pdf = requests.get(f"{BASE_URL}/api/reports/export?type=students&format=pdf")
    assert r_pdf.status_code == 200
    log("[OK] GET /api/reports/export (CSV & PDF) passed")

    log("\nALL 14 REST API CHECKS PASSED PERFECTLY ON THE LIVE BACKEND SERVER!")

if __name__ == "__main__":
    test_live_api()
