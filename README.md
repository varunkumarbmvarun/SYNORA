# 🎓 College Knowledge Base Using First-Order Logic (FOL)

A full-stack, enterprise-grade AI knowledge system for college academic management. Built with a pure Python First-Order Logic (FOL) reasoner implementing Robinson-style term unification, fixpoint Forward Chaining, SLD Backward Chaining, and Natural Language Query understanding.

---

## 🏛️ Architecture Overview

The system strictly decouples the presentation layer, the REST reasoning services, and persistent relational storage:

```
Streamlit Frontend (:8501)
        │
        │ HTTP / JSON (via requests)
        ▼
Flask REST API (:5000)
   ├── Knowledge Base Service (CRUD + Atomic Entity ↔ FOL Fact Sync)
   ├── FOL Engine
   │     ├── Terms (Constant, Variable, Atom, Rule)
   │     ├── Parser (Unicode & ASCII normalization, Safety validator)
   │     ├── Unifier (Martelli-Montanari term dereferencing)
   │     ├── Forward Chaining Engine (Deductive fixpoint loop)
   │     ├── Backward Chaining Engine (SLD Resolution with Loop Protection)
   │     ├── Query Parser (Regex/Grammar + Live Entity Catalog)
   │     └── Explanation Generator (Proof Tree text & CWA notes)
   └── Storage Engine (SQLite via SQLAlchemy + Cascade Constraints)
```

> **Design Principle**: The Streamlit frontend never connects directly to SQLite. All operations pass through the Flask REST API. If the backend is offline, Streamlit displays a clear recovery banner rather than crashing.

---

## 🔬 First-Order Logic (FOL) Foundations

### 1. Terms, Atoms, and Safety Conditions
- **Constants**: Uppercase-initial symbolic identifiers representing domain entities (e.g., `Ravi`, `AI`, `Meena`, `CSE`).
- **Variables**: Lowercase identifiers (e.g., `x`, `y`, `z`) representing unknowns.
- **Atoms**: A predicate with an arity matching its definition (Unary: `Student`, `Professor`, `Course`, `Department`, `Faculty`; Binary: `Enrolled`, `Teaches`, `BelongsTo`, `OfferedBy`, `Studies`, `HeadOf`, `Prerequisite`, `AssociatedWith`).
- **Safety Condition**: For any rule $\text{Body} \rightarrow \text{Head}$, every variable occurring in $\text{Head}$ must occur in at least one premise atom in $\text{Body}$. This guarantees all instantiated derived facts are ground constants.

### 2. Unification and Substitution
The reasoner applies structural unification with term dereferencing (`walk`):
- $\text{unify}(t_1, t_2, \theta) \to \theta'$
- Maintains consistent bindings: a variable $x$ bound to `Ravi` cannot later bind to `Rahul` in the same branch.
- Standardizes variables apart during SLD resolution by renaming rule variables with unique iteration suffixes ($x_1, y_1, \dots$).

### 3. Forward Chaining (Fixpoint Deduction)
- Iteratively tests all enabled rules against base and derived facts.
- Computes all satisfying substitutions via conjunctive backtracking.
- Instantiates ground heads, detects duplicates, logs derivation premises, and halts when an iteration yields 0 new facts (the deductive fixpoint).
- Idempotent: running forward inference multiple times produces 0 duplicate facts.

### 4. Backward Chaining (SLD Resolution)
- Goal-directed top-down theorem prover.
- Proves goals dynamically even before forward chaining is executed.
- Includes loop detection (active ancestor goal set) and depth-bounding (limit: 10).
- Produces a complete **Resolution Proof Tree** detailing each deduction step (fact matching vs rule expansion).

### 5. Closed-World Assumption (CWA)
- If a query refers to constants or predicates entirely absent from the Knowledge Base, the engine returns **`UNKNOWN`**.
- If all entities are known to the domain, but no resolution proof can be derived from the facts and active rules, the system resolves the query to **`FALSE`**.
- If a formal proof exists, it returns **`TRUE`** along with variable bindings and the proof tree.

---

## ⚙️ Predefined Rules in System

The database is seeded with 15 standard First-Order Logic rules (enabled by default):

| # | Rule Name | First-Order Logic Formal Representation |
|---|---|---|
| 1 | Enrolled implies Studies | $\forall x \forall y (\text{Enrolled}(x,y) \rightarrow \text{Studies}(x,y))$ |
| 2 | Professor implies Faculty | $\forall x (\text{Professor}(x) \rightarrow \text{Faculty}(x))$ |
| 3 | Teaches implies Professor | $\forall x \forall y (\text{Teaches}(x,y) \rightarrow \text{Professor}(x))$ |
| 4 | Teaches implies Course | $\forall x \forall y (\text{Teaches}(x,y) \rightarrow \text{Course}(y))$ |
| 5 | BelongsTo implies Department | $\forall x \forall y (\text{BelongsTo}(x,y) \rightarrow \text{Department}(y))$ |
| 6 | OfferedBy implies Course | $\forall x \forall y (\text{OfferedBy}(x,y) \rightarrow \text{Course}(x))$ |
| 7 | OfferedBy implies Department | $\forall x \forall y (\text{OfferedBy}(x,y) \rightarrow \text{Department}(y))$ |
| 8 | HeadOf implies Professor | $\forall x \forall y (\text{HeadOf}(x,y) \rightarrow \text{Professor}(x))$ |
| 9 | HeadOf implies Department | $\forall x \forall y (\text{HeadOf}(x,y) \rightarrow \text{Department}(y))$ |
| 10 | Prerequisite implies Course (x) | $\forall x \forall y (\text{Prerequisite}(x,y) \rightarrow \text{Course}(x))$ |
| 11 | Enrolled implies Student | $\forall x \forall y (\text{Enrolled}(x,y) \rightarrow \text{Student}(x))$ |
| 12 | Enrollment & Dept Association | $\forall x \forall y \forall z (\text{Enrolled}(x,y) \wedge \text{OfferedBy}(y,z) \rightarrow \text{AssociatedWith}(x,z))$ |
| 13 | BelongsTo implies AssociatedWith | $\forall x \forall y (\text{BelongsTo}(x,y) \rightarrow \text{AssociatedWith}(x,y))$ |
| 14 | HeadOf implies BelongsTo | $\forall x \forall y (\text{HeadOf}(x,y) \rightarrow \text{BelongsTo}(x,y))$ |
| 15 | Prerequisite implies Course (y) | $\forall x \forall y (\text{Prerequisite}(x,y) \rightarrow \text{Course}(y))$ |

---

## 🚀 Setup and Execution

### 1. Requirements Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### 2. Start the Backend API (:5000)
In your first terminal:
```bash
python backend/app.py
```
*The database and sample dataset (`college_kb.db`) are automatically seeded on startup.*

### 3. Start the Streamlit Frontend (:8501)
In a second terminal:
```bash
streamlit run frontend/app.py
```
*(Or `python -m streamlit run frontend/app.py`)*

Open your browser at **`http://localhost:8501`**.

---

## 🧪 Automated Acceptance Testing

Run pytest across the full suite (logic engine unit tests + REST API integration tests):
```bash
pytest backend/tests/
```
All 16 acceptance tests pass, verifying:
- Forward chaining fixpoint deduction & second-run idempotency.
- Backward chaining SLD resolution (`TRUE`, `FALSE`, `UNKNOWN`).
- Rule disabling/re-enabling effects.
- Multi-premise custom rules.
- Automatic Entity ↔ FOL Fact synchronization on create/update/delete.
- CSV and PDF export generation.

---

## 🌐 REST API Endpoints

All responses conform to a unified JSON envelope:
- **Success**: `{"success": true, "data": ..., "message": "..."}`
- **Error**: `{"success": false, "error": {"code": "...", "message": "...", "details": ...}}`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend status check |
| `GET` | `/api/dashboard/stats` | Aggregated statistics, metrics, and activity feed |
| `GET` | `/api/students` | List students with `?search=` and `?department=` filters |
| `POST` | `/api/students` | Create student & automatically sync FOL facts |
| `GET` | `/api/students/<id>` | Student details, enrolled courses, and linked facts |
| `PUT` | `/api/students/<id>` | Update student profile & update facts |
| `DELETE`| `/api/students/<id>` | Delete student & purge associated facts |
| `POST` | `/api/students/<id>/enroll` | Enroll student in course |
| `POST` | `/api/students/<id>/unenroll` | Unenroll student from course |
| `GET` | `/api/professors` | List professors |
| `POST` | `/api/professors` | Create professor & sync FOL facts |
| `GET` | `/api/professors/<id>` | Professor details & courses taught |
| `PUT` | `/api/professors/<id>` | Update professor |
| `DELETE`| `/api/professors/<id>` | Delete professor & purge associated facts |
| `POST` | `/api/professors/<id>/assign` | Assign course to professor |
| `POST` | `/api/professors/<id>/unassign` | Unassign course from professor |
| `GET` | `/api/courses` | List courses |
| `POST` | `/api/courses` | Create course & sync FOL facts |
| `GET` | `/api/courses/<id>` | Course details, prerequisites, and instructors |
| `PUT` | `/api/courses/<id>` | Update course |
| `DELETE`| `/api/courses/<id>` | Delete course |
| `POST` | `/api/courses/<id>/prerequisites` | Add prerequisite course link |
| `DELETE`| `/api/courses/<id>/prerequisites/<prereq_id>` | Remove prerequisite link |
| `GET` | `/api/departments` | List academic departments |
| `POST` | `/api/departments` | Create department & sync FOL facts |
| `GET` | `/api/departments/<id>` | Department members, head, and courses |
| `PUT` | `/api/departments/<id>` | Update department |
| `DELETE`| `/api/departments/<id>` | Delete department |
| `POST` | `/api/departments/<id>/set-head` | Assign department head professor |
| `GET` | `/api/facts` | Filtered list of facts with pagination |
| `POST` | `/api/facts` | Add manual ground fact (validated) |
| `PUT` | `/api/facts/<id>` | Update existing fact |
| `DELETE`| `/api/facts/<id>` | Delete fact |
| `POST` | `/api/facts/import` | Import facts JSON or reload sample dataset |
| `GET` | `/api/facts/export` | Export facts in CSV format |
| `GET` | `/api/rules` | List all system and custom rules |
| `POST` | `/api/rules` | Create custom rule (parsed and validated) |
| `PUT` | `/api/rules/<id>` | Toggle enabled/disabled or update rule |
| `DELETE`| `/api/rules/<id>` | Delete custom rule (predefined cannot be deleted) |
| `POST` | `/api/rules/test` | Dry-run rule against database without saving |
| `POST` | `/api/inference/forward` | Execute forward chaining fixpoint deduction |
| `POST` | `/api/inference/backward` | Execute backward chaining proof for a goal |
| `GET` | `/api/inference/results` | Historical inference run logs |
| `DELETE`| `/api/inference/inferred` | Clear derived inferred facts |
| `POST` | `/api/query` | Natural language question compiler and reasoner |
| `GET` | `/api/query/history` | Historical queries and reasoning traces |
| `DELETE`| `/api/query/history` | Clear query history |
| `GET` | `/api/knowledge-graph` | NetworkX/Plotly node and edge graph data |
| `GET` | `/api/reports/summary` | Analytics summary metrics |
| `GET` | `/api/reports/export` | Download official CSV and PDF reports |

---

## 💬 Sample Queries to Try in the Demo

You can type either natural English or direct FOL queries into the **Query System**:

1. **"Who teaches AI?"**  
   $\rightarrow \text{Teaches}(x, \text{AI})$  
   *Answer: Meena*

2. **"Which students study AI?"**  
   $\rightarrow \text{Studies}(x, \text{AI})$  
   *Answer: Ravi, Rahul, Priya* (proved via Rule 1: $\text{Enrolled} \to \text{Studies}$)

3. **"Is Ravi enrolled in AI?"**  
   $\rightarrow \text{Enrolled}(\text{Ravi}, \text{AI})$  
   *Answer: Yes, it holds (TRUE)*

4. **"Which professors belong to CSE?"**  
   $\rightarrow \text{BelongsTo}(x, \text{CSE}) \wedge \text{Professor}(x)$  
   *Answer: Meena, Kiran, Anand*

5. **"Which courses are offered by CSE?"**  
   $\rightarrow \text{OfferedBy}(x, \text{CSE})$  
   *Answer: AI, DSA, DBMS, CN, ML*

6. **"Who is the head of CSE?"**  
   $\rightarrow \text{HeadOf}(x, \text{CSE})$  
   *Answer: Meena*

7. **"Is Meena a professor?"**  
   $\rightarrow \text{Professor}(\text{Meena})$  
   *Answer: Yes, it holds (TRUE)*

8. **"Is Ravi associated with CSE?"**  
   $\rightarrow \text{AssociatedWith}(\text{Ravi}, \text{CSE})$  
   *Answer: Yes, it holds (TRUE)* (proved via Rule 12 or 13)

9. **"What are the prerequisites of ML?"**  
   $\rightarrow \text{Prerequisite}(x, \text{ML})$  
   *Answer: AI*

10. **"Who is Ravi's professor?"**  
    $\rightarrow \text{Studies}(\text{Ravi}, y) \wedge \text{Teaches}(x, y)$  
    *Answer: Meena*

11. **"Does Ravi study DBMS?"**  
    $\rightarrow \text{Studies}(\text{Ravi}, \text{DBMS})$  
    *Answer: No, it does not hold (FALSE under CWA)*

12. **"Is Ghost enrolled in AI?"**  
    $\rightarrow \text{Enrolled}(\text{Ghost}, \text{AI})$  
    *Answer: UNKNOWN (entity Ghost is outside the knowledge base)*

---

## 📁 Project Directory Structure

```
SYNORA/
├── backend/
│   ├── app.py                 # Flask app factory, CORS, logging, error handlers
│   ├── config.py              # Path configuration and environment settings
│   ├── database.py            # SQLite engine, scoped session, pragma foreign keys
│   ├── models.py              # SQLAlchemy models with cascade relations
│   ├── seed.py                # Idempotent loader with default data & 15 rules
│   ├── logic/
│   │   ├── terms.py           # Term, Constant, Variable, Atom, Rule dataclasses
│   │   ├── parser.py          # Unicode/ASCII rule and ground fact parser
│   │   ├── unifier.py         # FOL unification, dereferencing, conjunction matching
│   │   ├── forward_chaining.py# Fixpoint deductive engine with step tracking
│   │   ├── backward_chaining.py# SLD resolution with loop detection & proof trees
│   │   ├── query_parser.py    # Natural language compiler with live entity catalog
│   │   └── explain.py         # Human-readable explanation builder
│   ├── routes/
│   │   ├── students.py        # Student endpoints + enroll/unenroll
│   │   ├── professors.py      # Professor endpoints + course assignment
│   │   ├── courses.py         # Course catalog + prerequisite management
│   │   ├── departments.py     # Department endpoints + head assignment
│   │   ├── facts.py           # KB facts CRUD, import, and export
│   │   ├── rules.py           # FOL rule management + dry-run test
│   │   ├── inference.py       # Forward & backward chaining endpoints
│   │   ├── query.py           # NL query execution & history
│   │   ├── graph.py           # Knowledge graph topological node/edge data
│   │   ├── dashboard.py       # Real-time statistics & activity feed
│   │   └── reports.py         # CSV & PDF export endpoints
│   ├── services/
│   │   ├── sync_service.py    # Atomic Entity ↔ FOL Fact synchronization
│   │   ├── fact_service.py    # Fact database queries & import/export
│   │   ├── rule_service.py    # Rule persistence & dry-run testing
│   │   └── report_service.py  # ReportLab PDF & CSV generation
│   └── tests/
│       ├── test_logic.py      # Unit tests for the custom FOL reasoner
│       ├── test_api.py        # REST API endpoint acceptance tests
│       └── verify_endpoints.py# Live end-to-end server verification
├── frontend/
│   ├── app.py                 # Streamlit entrypoint, CSS theme, sidebar router
│   ├── api_client.py          # Centralized requests HTTP client
│   ├── components/
│   │   ├── ui.py              # Metric cards, status pills, headers, error panels
│   │   ├── charts.py          # Plotly distribution and composition charts
│   │   └── graph.py           # NetworkX topological layout rendered in Plotly
│   └── pages/
│       ├── dashboard.py       # Overview metrics, charts, activity logs, graph
│       ├── knowledge_base.py  # All facts, add, edit, delete, import, export
│       ├── students.py        # Students roster, detail, enrollment actions
│       ├── professors.py      # Faculty roster, detail, teaching assignments
│       ├── courses.py         # Courses catalog, detail, prerequisite graphs
│       ├── departments.py     # Departments roster, detail, leadership actions
│       ├── fol_rules.py       # Rules table, toggling, parse validation, dry-run
│       ├── inference.py       # Forward fixpoint & backward SLD visualizer
│       ├── query.py           # Interactive NL question answering & proof trees
│       ├── knowledge_graph.py # Interactive NetworkX topological graph
│       ├── reports.py         # Multi-category CSV & PDF export center
│       └── settings.py        # API configuration, reset DB, system diagnosis
├── requirements.txt
└── README.md
```

---

## 🎯 Viva & Demo Walkthrough Script

1. **Architecture Explanation**:
   - Point out that Streamlit is a pure client interacting with the Flask REST API via JSON.
   - Show that entity mutations (e.g. creating a student or assigning a course) automatically synchronize into First-Order Logic facts (`Student`, `BelongsTo`, `Enrolled`, etc.) inside the same database transaction.

2. **Logic Engine Demonstration**:
   - Go to **FOL Rules**: show the 15 system rules with Unicode logical operators ($\forall, \rightarrow, \wedge$).
   - Switch to **Test Rule**: paste `Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)` and run the dry run. Explain how conjunctive body matching unifies variables across multiple premises to discover new facts without altering the database.

3. **Inference Demonstration**:
   - Go to **Inference Engine** $\rightarrow$ **Backward Chaining**:
     - Prove `Studies(Ravi, AI)` $\rightarrow$ **TRUE**. Expand the proof tree to show that Rule 1 unified with the ground fact `Enrolled(Ravi, AI)`.
     - Prove `Studies(Ravi, DBMS)` $\rightarrow$ **FALSE**. Explain how the Closed-World Assumption operates.
     - Prove `Studies(Ghost, AI)` $\rightarrow$ **UNKNOWN**. Explain how entity boundary checking differentiates unknown terms from false facts.
   - Switch to **Forward Chaining**:
     - Click **Run Forward Inference Engine**. Highlight the iteration steps ($0 \to \text{fixpoint}$) and newly inferred facts. Run it a second time to demonstrate idempotency (0 new facts).

4. **Natural Language Query System**:
   - Go to **Query System** and click *"Which students study AI?"*.
   - Show how the NLP parser mapped the phrase into $\text{Studies}(x, \text{AI})$, resolved the alias `AI`, executed backward resolution, returned the answers `Ravi, Rahul, Priya`, and generated the natural-language explanation and proof tree.

5. **Reports and Knowledge Graph**:
   - Open **Knowledge Graph**: demonstrate the spring layout, filter edges by predicate, and search for `Meena` to highlight her node.
   - Open **Reports**: click **Download as PDF** on Students or Knowledge Base to demonstrate dynamic, styled ReportLab PDF generation.
#   S Y N O R A  
 