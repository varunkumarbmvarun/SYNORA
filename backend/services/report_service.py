import io
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models import (
    Student, Professor, Course, Department, Fact, Rule,
    InferenceResult, QueryHistory, ActivityLog
)
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class ReportService:
    @staticmethod
    def get_summary_stats(session: Session) -> Dict[str, Any]:
        students_count = session.query(Student).count()
        professors_count = session.query(Professor).count()
        courses_count = session.query(Course).count()
        departments_count = session.query(Department).count()
        facts_count = session.query(Fact).count()
        inferred_facts_count = session.query(Fact).filter(Fact.is_inferred == True).count()
        base_facts_count = facts_count - inferred_facts_count
        rules_count = session.query(Rule).count()
        enabled_rules_count = session.query(Rule).filter(Rule.enabled == True).count()
        queries_count = session.query(QueryHistory).count()
        inference_runs = session.query(InferenceResult).count()

        # Facts by predicate
        facts = session.query(Fact).all()
        by_predicate = {}
        for f in facts:
            by_predicate[f.predicate] = by_predicate.get(f.predicate, 0) + 1

        # Students per department
        depts = session.query(Department).all()
        students_per_dept = {d.code: len(d.students) for d in depts}
        courses_per_dept = {d.code: len(d.courses) for d in depts}

        # Courses per professor
        profs = session.query(Professor).all()
        courses_per_prof = {p.name: len(p.courses) for p in profs}

        return {
            "students_count": students_count,
            "professors_count": professors_count,
            "courses_count": courses_count,
            "departments_count": departments_count,
            "facts_count": facts_count,
            "base_facts_count": base_facts_count,
            "inferred_facts_count": inferred_facts_count,
            "rules_count": rules_count,
            "enabled_rules_count": enabled_rules_count,
            "queries_count": queries_count,
            "inference_runs": inference_runs,
            "facts_by_predicate": by_predicate,
            "students_per_department": students_per_dept,
            "courses_per_department": courses_per_dept,
            "courses_per_professor": courses_per_prof
        }

    @staticmethod
    def export_csv(session: Session, report_type: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "students":
            writer.writerow(["ID", "Code", "Name", "Email", "Semester", "Status", "Department", "Courses"])
            for s in session.query(Student).all():
                courses = ", ".join(c.alias for c in s.courses)
                writer.writerow([s.id, s.student_code, s.name, s.email, s.semester, s.status, s.department.code, courses])

        elif report_type == "professors":
            writer.writerow(["ID", "Code", "Name", "Email", "Specialization", "Department", "Courses"])
            for p in session.query(Professor).all():
                courses = ", ".join(c.alias for c in p.courses)
                writer.writerow([p.id, p.prof_code, p.name, p.email, p.specialization, p.department.code, courses])

        elif report_type == "courses":
            writer.writerow(["ID", "Code", "Name", "Alias", "Credits", "Department", "Professors", "Students", "Prerequisites"])
            for c in session.query(Course).all():
                profs = ", ".join(p.name for p in c.professors)
                prereqs = ", ".join(p.alias for p in c.prerequisites)
                writer.writerow([c.id, c.course_code, c.name, c.alias, c.credits, c.department.code, profs, len(c.students), prereqs])

        elif report_type == "departments":
            writer.writerow(["ID", "Code", "Name", "Head Professor", "Professors Count", "Students Count", "Courses Count"])
            for d in session.query(Department).all():
                head = d.head_professor.name if d.head_professor else "None"
                writer.writerow([d.id, d.code, d.name, head, len(d.professors), len(d.students), len(d.courses)])

        elif report_type == "facts":
            writer.writerow(["ID", "Predicate", "Arg1", "Arg2", "FOL", "IsInferred", "Source", "RuleID"])
            for f in session.query(Fact).all():
                writer.writerow([f.id, f.predicate, f.arg1, f.arg2 or "", f.to_fol(), f.is_inferred, f.source, f.source_rule_id or ""])

        elif report_type == "inference":
            writer.writerow(["ID", "RunType", "Goal", "Iterations", "NewFactsCount", "ExecutionMs", "CreatedAt"])
            for i in session.query(InferenceResult).all():
                writer.writerow([i.id, i.run_type, i.goal or "", i.iterations, i.new_facts_count, i.execution_ms, i.created_at])

        elif report_type == "queries":
            writer.writerow(["ID", "Question", "LogicalQuery", "TruthValue", "Answer", "CreatedAt"])
            for q in session.query(QueryHistory).all():
                writer.writerow([q.id, q.question, q.logical_query, q.truth_value, q.answer, q.created_at])

        return output.getvalue()

    @staticmethod
    def export_pdf(session: Session, report_type: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name='DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1E293B')
        )
        subtitle_style = ParagraphStyle(
            name='DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B')
        )
        cell_style = ParagraphStyle(
            name='Cell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11
        )
        header_cell_style = ParagraphStyle(
            name='HeaderCell',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke
        )

        elements = []
        elements.append(Paragraph(f"College FOL Knowledge Base Report: {report_type.capitalize()}", title_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | System: Antigravity Logic Engine", subtitle_style))
        elements.append(Spacer(1, 15))

        data: List[List[Any]] = []

        if report_type == "students":
            headers = ["Code", "Name", "Email", "Sem", "Status", "Dept", "Courses"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for s in session.query(Student).all():
                courses = ", ".join(c.alias for c in s.courses) or "None"
                row = [s.student_code, s.name, s.email, str(s.semester), s.status, s.department.code, courses]
                data.append([Paragraph(c, cell_style) for c in row])

        elif report_type == "professors":
            headers = ["Code", "Name", "Email", "Specialization", "Dept", "Courses"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for p in session.query(Professor).all():
                courses = ", ".join(c.alias for c in p.courses) or "None"
                row = [p.prof_code, p.name, p.email, p.specialization, p.department.code, courses]
                data.append([Paragraph(c, cell_style) for c in row])

        elif report_type == "courses":
            headers = ["Code", "Name", "Alias", "Credits", "Dept", "Instructors", "Prereqs"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for c in session.query(Course).all():
                profs = ", ".join(p.name for p in c.professors) or "None"
                prereqs = ", ".join(p.alias for p in c.prerequisites) or "None"
                row = [c.course_code, c.name, c.alias, str(c.credits), c.department.code, profs, prereqs]
                data.append([Paragraph(cell, cell_style) for cell in row])

        elif report_type == "departments":
            headers = ["Code", "Name", "Head Professor", "Professors", "Students", "Courses"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for d in session.query(Department).all():
                head = d.head_professor.name if d.head_professor else "None"
                row = [d.code, d.name, head, str(len(d.professors)), str(len(d.students)), str(len(d.courses))]
                data.append([Paragraph(cell, cell_style) for cell in row])

        elif report_type == "facts":
            headers = ["ID", "FOL Fact", "Type", "Source"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for f in session.query(Fact).limit(100).all():
                ftype = "Inferred" if f.is_inferred else "Base"
                row = [str(f.id), f.to_fol(), ftype, f.source]
                data.append([Paragraph(cell, cell_style) for cell in row])

        elif report_type == "inference":
            headers = ["ID", "Type", "Goal", "Iters", "New Facts", "Time (ms)", "Date"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for i in session.query(InferenceResult).limit(50).all():
                row = [str(i.id), i.run_type, i.goal or "-", str(i.iterations), str(i.new_facts_count), f"{i.execution_ms}ms", str(i.created_at.strftime("%Y-%m-%d %H:%M"))]
                data.append([Paragraph(cell, cell_style) for cell in row])

        elif report_type == "queries":
            headers = ["ID", "Question", "Logical Query", "Value", "Answer"]
            data.append([Paragraph(h, header_cell_style) for h in headers])
            for q in session.query(QueryHistory).limit(50).all():
                row = [str(q.id), q.question, q.logical_query, q.truth_value, q.answer[:60]]
                data.append([Paragraph(cell, cell_style) for cell in row])

        if data:
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("No records found for this category.", subtitle_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
