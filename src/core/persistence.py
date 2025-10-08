from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional, List, Dict, Any
from datetime import datetime

class NodeRow(SQLModel, table=True):
    id: str = Field(primary_key=True)
    parent_id: str | None = Field(default=None, index=True)
    type: str
    stage: int
    prompt: str
    plan: str | None = None
    code_path: str | None = None
    results_path: str | None = None
    figs_paths: str | None = None  # JSON string list
    score: float | None = None
    visits: int = 0
    value_sum: float = 0.0
    status: str = "PENDING"
    meta: str | None = None        # JSON string dict
    created_at: datetime = Field(default_factory=datetime.utcnow)

def init_db(sqlite_url: str):
    engine = create_engine(sqlite_url, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

def upsert_node(engine, row: NodeRow):
    with Session(engine) as s:
        s.merge(row)
        s.commit()

def get_node(engine, node_id: str) -> NodeRow | None:
    with Session(engine) as s:
        q = s.exec(select(NodeRow).where(NodeRow.id == node_id))
        return q.first()

def update_visits_value(engine, node_id: str, visits_inc: int, value_inc: float):
    with Session(engine) as s:
        row = s.get(NodeRow, node_id)
        if not row:
            return
        row.visits += visits_inc
        row.value_sum += value_inc
        s.add(row)
        s.commit()

def export_node(row: NodeRow) -> Dict[str, Any]:
    return {
        "id": row.id,
        "parent_id": row.parent_id,
        "type": row.type,
        "stage": row.stage,
        "prompt": row.prompt,
        "plan": row.plan,
        "code_path": row.code_path,
        "results_path": row.results_path,
        "figs_paths": row.figs_paths,
        "score": row.score,
        "visits": row.visits,
        "value_sum": row.value_sum,
        "status": row.status,
        "meta": row.meta,
        "created_at": row.created_at.isoformat(),
    }
