import csv
import io
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.models import Fact, Rule
from backend.logic.parser import parse_fact, ParseError
from backend.services.sync_service import SyncService


class FactService:
    @staticmethod
    def get_facts(
        session: Session,
        predicate: Optional[str] = None,
        search: Optional[str] = None,
        is_inferred: Optional[bool] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        q = session.query(Fact)

        if predicate:
            q = q.filter(Fact.predicate == predicate)
        if is_inferred is not None:
            q = q.filter(Fact.is_inferred == is_inferred)
        if source:
            q = q.filter(Fact.source == source)
        if search:
            term = f"%{search.strip()}%"
            q = q.filter(
                or_(
                    Fact.predicate.ilike(term),
                    Fact.arg1.ilike(term),
                    Fact.arg2.ilike(term)
                )
            )

        total = q.count()
        facts = q.order_by(Fact.predicate, Fact.arg1).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "facts": [f.to_dict() for f in facts]
        }

    @staticmethod
    def create_fact(
        session: Session,
        predicate: str,
        arg1: str,
        arg2: Optional[str] = None,
        source: str = "manual"
    ) -> Fact:
        # Validate format
        norm_arg2 = arg2.strip() if arg2 and arg2.strip() else None
        arg1 = arg1.strip()
        fol_str = f"{predicate}({arg1}, {norm_arg2})" if norm_arg2 else f"{predicate}({arg1})"

        try:
            parsed = parse_fact(fol_str)
        except ParseError as e:
            raise ValueError(str(e))

        # Check duplicate
        q = session.query(Fact).filter(Fact.predicate == parsed.predicate, Fact.arg1 == parsed.terms[0].name)
        if len(parsed.terms) > 1:
            q = q.filter(Fact.arg2 == parsed.terms[1].name)
        else:
            q = q.filter(Fact.arg2.is_(None))

        existing = q.first()
        if existing:
            raise ValueError(f"Fact '{fol_str}' already exists in knowledge base.")

        fact = Fact(
            predicate=parsed.predicate,
            arg1=parsed.terms[0].name,
            arg2=parsed.terms[1].name if len(parsed.terms) > 1 else None,
            is_inferred=False,
            source=source
        )
        session.add(fact)
        session.flush()

        SyncService.log_activity(session, "CREATE", "Fact", f"Created fact {fact.to_fol()}")
        return fact

    @staticmethod
    def update_fact(
        session: Session,
        fact_id: int,
        predicate: str,
        arg1: str,
        arg2: Optional[str] = None
    ) -> Fact:
        fact = session.get(Fact, fact_id)
        if not fact:
            raise ValueError(f"Fact with ID {fact_id} not found.")

        norm_arg2 = arg2.strip() if arg2 and arg2.strip() else None
        arg1 = arg1.strip()
        fol_str = f"{predicate}({arg1}, {norm_arg2})" if norm_arg2 else f"{predicate}({arg1})"

        try:
            parsed = parse_fact(fol_str)
        except ParseError as e:
            raise ValueError(str(e))

        fact.predicate = parsed.predicate
        fact.arg1 = parsed.terms[0].name
        fact.arg2 = parsed.terms[1].name if len(parsed.terms) > 1 else None
        session.flush()

        SyncService.log_activity(session, "UPDATE", "Fact", f"Updated fact ID {fact_id} to {fact.to_fol()}")
        return fact

    @staticmethod
    def delete_fact(session: Session, fact_id: int) -> bool:
        fact = session.get(Fact, fact_id)
        if not fact:
            raise ValueError(f"Fact with ID {fact_id} not found.")

        fol_str = fact.to_fol()
        session.delete(fact)
        SyncService.log_activity(session, "DELETE", "Fact", f"Deleted fact {fol_str}")
        return True

    @staticmethod
    def clear_inferred_facts(session: Session) -> int:
        count = session.query(Fact).filter(Fact.is_inferred == True).delete(synchronize_session=False)
        SyncService.log_activity(session, "CLEAR", "Inference", f"Cleared {count} derived inferred facts")
        return count

    @staticmethod
    def export_facts_csv(session: Session) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "predicate", "arg1", "arg2", "fol", "is_inferred", "source", "source_rule_id", "created_at"])
        facts = session.query(Fact).order_by(Fact.id).all()
        for f in facts:
            writer.writerow([
                f.id, f.predicate, f.arg1, f.arg2 or "", f.to_fol(),
                f.is_inferred, f.source, f.source_rule_id or "",
                f.created_at.isoformat() if f.created_at else ""
            ])
        return output.getvalue()

    @staticmethod
    def export_facts_json(session: Session) -> List[Dict[str, Any]]:
        facts = session.query(Fact).order_by(Fact.id).all()
        return [f.to_dict() for f in facts]

    @staticmethod
    def import_facts(session: Session, facts_data: List[Dict[str, Any]]) -> Dict[str, int]:
        imported = 0
        skipped = 0
        for item in facts_data:
            pred = item.get("predicate")
            arg1 = item.get("arg1")
            arg2 = item.get("arg2")
            if not pred or not arg1:
                # Try parsing raw fol
                fol = item.get("fol")
                if fol:
                    try:
                        atom = parse_fact(fol)
                        pred = atom.predicate
                        arg1 = atom.terms[0].name
                        arg2 = atom.terms[1].name if len(atom.terms) > 1 else None
                    except Exception:
                        skipped += 1
                        continue
                else:
                    skipped += 1
                    continue
            try:
                FactService.create_fact(
                    session=session,
                    predicate=pred,
                    arg1=arg1,
                    arg2=arg2,
                    source=item.get("source", "import")
                )
                imported += 1
            except Exception:
                skipped += 1

        SyncService.log_activity(session, "IMPORT", "Fact", f"Imported {imported} facts, skipped {skipped}")
        return {"imported": imported, "skipped": skipped}
