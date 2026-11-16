import os
import requests
from typing import Dict, Any, Optional, Tuple


class APIClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get("BACKEND_URL", "http://localhost:5000")).rstrip('/')
        self.session = requests.Session()
        self.timeout = 10

    def set_base_url(self, url: str):
        self.base_url = url.rstrip('/')

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.request(method, url, **kwargs)
            try:
                data = resp.json()
            except Exception:
                data = {"success": resp.status_code < 400, "message": resp.text}

            if not resp.ok and isinstance(data, dict) and "error" not in data:
                data = {
                    "success": False,
                    "error": {
                        "code": f"HTTP_{resp.status_code}",
                        "message": data.get("message", f"Request failed with status {resp.status_code}"),
                        "details": data
                    }
                }
            return data
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": {
                    "code": "CONNECTION_ERROR",
                    "message": f"Backend not reachable at {self.base_url}. Run 'python backend/app.py' to start the server.",
                    "details": None
                }
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": {
                    "code": "TIMEOUT",
                    "message": f"Request to {url} timed out.",
                    "details": None
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "CLIENT_ERROR",
                    "message": str(e),
                    "details": None
                }
            }

    # Health
    def check_health(self) -> Dict[str, Any]:
        return self._request("GET", "/api/health")

    # Dashboard
    def get_dashboard_stats(self) -> Dict[str, Any]:
        return self._request("GET", "/api/dashboard/stats")

    # Students
    def get_students(self, search: str = "", department: str = "") -> Dict[str, Any]:
        return self._request("GET", "/api/students", params={"search": search, "department": department})

    def get_student(self, student_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/students/{student_id}")

    def create_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/students", json=data)

    def update_student(self, student_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/students/{student_id}", json=data)

    def delete_student(self, student_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/students/{student_id}")

    def enroll_student(self, student_id: int, course_alias: str) -> Dict[str, Any]:
        return self._request("POST", f"/api/students/{student_id}/enroll", json={"course_alias": course_alias})

    def unenroll_student(self, student_id: int, course_alias: str) -> Dict[str, Any]:
        return self._request("POST", f"/api/students/{student_id}/unenroll", json={"course_alias": course_alias})

    # Professors
    def get_professors(self, search: str = "", department: str = "") -> Dict[str, Any]:
        return self._request("GET", "/api/professors", params={"search": search, "department": department})

    def get_professor(self, prof_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/professors/{prof_id}")

    def create_professor(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/professors", json=data)

    def update_professor(self, prof_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/professors/{prof_id}", json=data)

    def delete_professor(self, prof_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/professors/{prof_id}")

    def assign_professor_course(self, prof_id: int, course_alias: str) -> Dict[str, Any]:
        return self._request("POST", f"/api/professors/{prof_id}/assign", json={"course_alias": course_alias})

    def unassign_professor_course(self, prof_id: int, course_alias: str) -> Dict[str, Any]:
        return self._request("POST", f"/api/professors/{prof_id}/unassign", json={"course_alias": course_alias})

    # Courses
    def get_courses(self, search: str = "", department: str = "") -> Dict[str, Any]:
        return self._request("GET", "/api/courses", params={"search": search, "department": department})

    def get_course(self, course_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/courses/{course_id}")

    def create_course(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/courses", json=data)

    def update_course(self, course_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/courses/{course_id}", json=data)

    def delete_course(self, course_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/courses/{course_id}")

    def add_prerequisite(self, course_id: int, prereq_alias: str) -> Dict[str, Any]:
        return self._request("POST", f"/api/courses/{course_id}/prerequisites", json={"prerequisite_alias": prereq_alias})

    def remove_prerequisite(self, course_id: int, prereq_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/courses/{course_id}/prerequisites/{prereq_id}")

    # Departments
    def get_departments(self) -> Dict[str, Any]:
        return self._request("GET", "/api/departments")

    def get_department(self, dept_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/departments/{dept_id}")

    def create_department(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/departments", json=data)

    def update_department(self, dept_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/departments/{dept_id}", json=data)

    def delete_department(self, dept_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/departments/{dept_id}")

    def set_department_head(self, dept_id: int, prof_name: str) -> Dict[str, Any]:
        return self._request("POST", f"/api/departments/{dept_id}/set-head", json={"professor_name": prof_name})

    # Facts
    def get_facts(
        self,
        predicate: Optional[str] = None,
        search: Optional[str] = None,
        inferred: Optional[bool] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        params = {"page": page, "page_size": page_size}
        if predicate:
            params["predicate"] = predicate
        if search:
            params["search"] = search
        if inferred is not None:
            params["inferred"] = str(inferred).lower()
        if source:
            params["source"] = source
        return self._request("GET", "/api/facts", params=params)

    def create_fact(self, predicate: str, arg1: str, arg2: Optional[str] = None) -> Dict[str, Any]:
        return self._request("POST", "/api/facts", json={"predicate": predicate, "arg1": arg1, "arg2": arg2})

    def update_fact(self, fact_id: int, predicate: str, arg1: str, arg2: Optional[str] = None) -> Dict[str, Any]:
        return self._request("PUT", f"/api/facts/{fact_id}", json={"predicate": predicate, "arg1": arg1, "arg2": arg2})

    def delete_fact(self, fact_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/facts/{fact_id}")

    def import_facts(self, facts_list: list) -> Dict[str, Any]:
        return self._request("POST", "/api/facts/import", json={"facts": facts_list})

    def seed_sample_data(self) -> Dict[str, Any]:
        return self._request("POST", "/api/facts/import", json={"action": "seed"})

    # Rules
    def get_rules(self) -> Dict[str, Any]:
        return self._request("GET", "/api/rules")

    def create_rule(self, name: str, rule_text: str, enabled: bool = True) -> Dict[str, Any]:
        return self._request("POST", "/api/rules", json={"name": name, "rule_text": rule_text, "enabled": enabled})

    def update_rule(self, rule_id: int, name: Optional[str] = None, rule_text: Optional[str] = None, enabled: Optional[bool] = None) -> Dict[str, Any]:
        data = {}
        if name is not None:
            data["name"] = name
        if rule_text is not None:
            data["rule_text"] = rule_text
        if enabled is not None:
            data["enabled"] = enabled
        return self._request("PUT", f"/api/rules/{rule_id}", json=data)

    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/rules/{rule_id}")

    def test_rule(self, rule_text: str) -> Dict[str, Any]:
        return self._request("POST", "/api/rules/test", json={"rule_text": rule_text})

    # Inference
    def run_forward_inference(self) -> Dict[str, Any]:
        return self._request("POST", "/api/inference/forward")

    def run_backward_inference(self, goal: str) -> Dict[str, Any]:
        return self._request("POST", "/api/inference/backward", json={"goal": goal})

    def get_inference_results(self, limit: int = 20) -> Dict[str, Any]:
        return self._request("GET", "/api/inference/results", params={"limit": limit})

    def clear_inferred_facts(self) -> Dict[str, Any]:
        return self._request("DELETE", "/api/inference/inferred")

    # Query
    def execute_query(self, question: str) -> Dict[str, Any]:
        return self._request("POST", "/api/query", json={"question": question})

    def get_query_history(self, limit: int = 50) -> Dict[str, Any]:
        return self._request("GET", "/api/query/history", params={"limit": limit})

    def clear_query_history(self) -> Dict[str, Any]:
        return self._request("DELETE", "/api/query/history")

    # Knowledge Graph
    def get_knowledge_graph(self, predicates: Optional[str] = None, include_inferred: bool = True) -> Dict[str, Any]:
        params = {"include_inferred": str(include_inferred).lower()}
        if predicates:
            params["predicates"] = predicates
        return self._request("GET", "/api/knowledge-graph", params=params)

    # Reports
    def get_reports_summary(self) -> Dict[str, Any]:
        return self._request("GET", "/api/reports/summary")

    def export_report_bytes(self, report_type: str, fmt: str) -> Tuple[Optional[bytes], Optional[str]]:
        url = f"{self.base_url}/api/reports/export"
        try:
            resp = self.session.get(url, params={"type": report_type, "format": fmt}, timeout=self.timeout)
            if resp.ok:
                return resp.content, None
            return None, f"Failed: HTTP {resp.status_code}"
        except Exception as e:
            return None, str(e)


# Global singleton instance
api = APIClient()
