import pytest
import json
from backend.app import create_app
from backend.database import init_db, db_session
from backend.seed import seed_database
from backend.models import Student, Fact


@pytest.fixture(scope='module')
def test_client():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        init_db()
        seed_database(force_reset=True)
        with app.test_client() as client:
            yield client


def test_health_check(test_client):
    res = test_client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'healthy'


def test_dashboard_stats(test_client):
    res = test_client.get('/api/dashboard/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['students_count'] >= 3
    assert data['data']['rules_count'] == 15


def test_students_crud_and_sync(test_client):
    # 1. Create a student via API
    new_student_data = {
        "student_code": "USN_TEST_99",
        "name": "Kavya",
        "email": "kavya@college.edu",
        "semester": 3,
        "department_id": 1,
        "status": "Active"
    }
    post_res = test_client.post('/api/students', json=new_student_data)
    assert post_res.status_code == 201
    post_json = post_res.get_json()
    assert post_json['success'] is True
    student_id = post_json['data']['id']

    # Verify fact Student(Kavya) was created
    facts_res = test_client.get('/api/facts?predicate=Student&search=Kavya')
    facts_json = facts_res.get_json()
    assert facts_json['data']['total'] >= 1
    assert any(f['arg1'] == 'Kavya' for f in facts_json['data']['facts'])

    # 2. Get student detail
    get_res = test_client.get(f'/api/students/{student_id}')
    assert get_res.status_code == 200
    assert get_res.get_json()['data']['name'] == 'Kavya'

    # 3. Enroll Kavya in AI
    enroll_res = test_client.post(f'/api/students/{student_id}/enroll', json={"course_alias": "AI"})
    assert enroll_res.status_code == 200

    # Verify Enrolled(Kavya, AI) fact exists
    enr_fact_res = test_client.get('/api/facts?predicate=Enrolled&search=Kavya')
    assert enr_fact_res.get_json()['data']['total'] >= 1

    # 4. Delete Kavya
    del_res = test_client.delete(f'/api/students/{student_id}')
    assert del_res.status_code == 200

    # Verify facts mentioning Kavya are gone
    after_facts = test_client.get('/api/facts?search=Kavya').get_json()
    assert after_facts['data']['total'] == 0


def test_rules_crud_and_test(test_client):
    # 1. Test a valid rule
    rule_data = {"rule_text": "Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)"}
    test_res = test_client.post('/api/rules/test', json=rule_data)
    assert test_res.status_code == 200
    test_json = test_res.get_json()
    assert test_json['success'] is True
    assert test_json['data']['new_facts_count'] > 0

    # 2. Test invalid rule (unknown predicate) -> 422
    bad_rule = {"rule_text": "FakePredicate(x) -> Studies(x, AI)"}
    bad_res = test_client.post('/api/rules/test', json=bad_rule)
    assert bad_res.status_code == 422
    assert bad_res.get_json()['success'] is False

    # 3. Toggle predefined rule
    toggle_res = test_client.put('/api/rules/1', json={"enabled": False})
    assert toggle_res.status_code == 200
    assert toggle_res.get_json()['data']['enabled'] is False

    # Restore rule 1
    test_client.put('/api/rules/1', json={"enabled": True})


def test_inference_endpoints(test_client):
    # 1. Forward chaining
    fwd_res = test_client.post('/api/inference/forward')
    assert fwd_res.status_code == 200
    fwd_json = fwd_res.get_json()
    assert fwd_json['success'] is True
    assert fwd_json['data']['new_facts_count'] > 0

    # 2. Backward chaining
    bwd_res = test_client.post('/api/inference/backward', json={"goal": "Studies(Ravi, AI)"})
    assert bwd_res.status_code == 200
    bwd_json = bwd_res.get_json()
    assert bwd_json['data']['truth_value'] == "TRUE"

    # 3. Get results history
    res_list = test_client.get('/api/inference/results')
    assert res_list.status_code == 200
    assert len(res_list.get_json()['data']) >= 2

    # 4. Clear inferred
    clr_res = test_client.delete('/api/inference/inferred')
    assert clr_res.status_code == 200


def test_natural_language_query_endpoint(test_client):
    query_payload = {"question": "Which students study AI?"}
    res = test_client.post('/api/query', json=query_payload)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['truth_value'] == "TRUE"
    assert "Ravi" in data['answers']
    assert "Rahul" in data['answers']
    assert "Priya" in data['answers']
    assert len(data['rules_applied']) > 0

    # History
    hist_res = test_client.get('/api/query/history')
    assert hist_res.status_code == 200
    assert len(hist_res.get_json()['data']) >= 1


def test_knowledge_graph_endpoint(test_client):
    res = test_client.get('/api/knowledge-graph')
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['total_nodes'] > 0
    assert data['total_edges'] > 0


def test_export_reports(test_client):
    # CSV export
    csv_res = test_client.get('/api/reports/export?type=students&format=csv')
    assert csv_res.status_code == 200
    assert b"Name" in csv_res.data
    assert b"Ravi" in csv_res.data

    # PDF export
    pdf_res = test_client.get('/api/reports/export?type=students&format=pdf')
    assert pdf_res.status_code == 200
    assert pdf_res.headers['Content-Type'] == 'application/pdf'
    assert pdf_res.data.startswith(b'%PDF')
