"""
Router: Consorcios + Unidades
GET  /api/consorcios
POST /api/consorcios
PUT  /api/consorcios/{id}
DELETE /api/consorcios/{id}
GET  /api/consorcios/{id}/unidades
POST /api/consorcios/{id}/unidades
PUT  /api/unidades/{id}
DELETE /api/unidades/{id}
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sqlite3

from api.database import get_db, rows_to_list, row_to_dict
from api.schemas import ConsorcioOut, ConsorcioCreate, UnidadOut, UnidadCreate, MessageOut

router = APIRouter(tags=["Consorcios"])


# ─── CONSORCIOS ────────────────────────────────────────────────────────────────

@router.get("/consorcios", response_model=List[ConsorcioOut])
def list_consorcios(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM consorcios ORDER BY nombre").fetchall()
    return rows_to_list(rows)


@router.get("/consorcios/{cid}", response_model=ConsorcioOut)
def get_consorcio(cid: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Consorcio no encontrado")
    return row_to_dict(row)


@router.post("/consorcios", response_model=ConsorcioOut, status_code=201)
def create_consorcio(body: ConsorcioCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO consorcios(nombre,cuit,direccion,unidades,reserva_pct,dia_vto) VALUES(?,?,?,?,?,?)",
        (body.nombre, body.cuit, body.direccion, body.unidades, body.reserva_pct, body.dia_vto)
    )
    row = db.execute("SELECT * FROM consorcios WHERE id=?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.put("/consorcios/{cid}", response_model=ConsorcioOut)
def update_consorcio(cid: int, body: ConsorcioCreate, db: sqlite3.Connection = Depends(get_db)):
    db.execute(
        "UPDATE consorcios SET nombre=?,cuit=?,direccion=?,unidades=?,reserva_pct=?,dia_vto=? WHERE id=?",
        (body.nombre, body.cuit, body.direccion, body.unidades, body.reserva_pct, body.dia_vto, cid)
    )
    row = db.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Consorcio no encontrado")
    return row_to_dict(row)


@router.delete("/consorcios/{cid}", response_model=MessageOut)
def delete_consorcio(cid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM consorcios WHERE id=?", (cid,))
    return {"ok": True, "message": f"Consorcio {cid} eliminado"}


# ─── UNIDADES ──────────────────────────────────────────────────────────────────

@router.get("/consorcios/{cid}/unidades", response_model=List[UnidadOut])
def list_unidades(cid: int, db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)",
        (cid,)
    ).fetchall()
    return rows_to_list(rows)


@router.post("/consorcios/{cid}/unidades", response_model=UnidadOut, status_code=201)
def create_unidad(cid: int, body: UnidadCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO unidades(consorcio_id,unidad,piso,dpto,propietario,inquilino,coef_a,coef_b,coef_c,email) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (cid, body.unidad, body.piso, body.dpto, body.propietario,
         body.inquilino, body.coef_a, body.coef_b, body.coef_c, body.email)
    )
    row = db.execute("SELECT * FROM unidades WHERE id=?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.put("/unidades/{uid}", response_model=UnidadOut)
def update_unidad(uid: int, body: UnidadCreate, db: sqlite3.Connection = Depends(get_db)):
    db.execute(
        "UPDATE unidades SET unidad=?,piso=?,dpto=?,propietario=?,inquilino=?,coef_a=?,coef_b=?,coef_c=?,email=? WHERE id=?",
        (body.unidad, body.piso, body.dpto, body.propietario,
         body.inquilino, body.coef_a, body.coef_b, body.coef_c, body.email, uid)
    )
    row = db.execute("SELECT * FROM unidades WHERE id=?", (uid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return row_to_dict(row)


@router.delete("/unidades/{uid}", response_model=MessageOut)
def delete_unidad(uid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM unidades WHERE id=?", (uid,))
    return {"ok": True, "message": f"Unidad {uid} eliminada"}


# ─── PERIODOS disponibles para un consorcio ────────────────────────────────────

@router.get("/consorcios/{cid}/periodos")
def list_periodos(cid: int, db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT DISTINCT periodo FROM gastos WHERE consorcio_id=? "
        "UNION SELECT DISTINCT g.periodo FROM pagos p "
        "JOIN unidades u ON p.unidad_id=u.id JOIN gastos g ON g.consorcio_id=u.consorcio_id AND g.periodo=p.periodo "
        "WHERE u.consorcio_id=? ORDER BY periodo DESC",
        (cid, cid)
    ).fetchall()
    periodos = [r[0] for r in rows]
    # Asegurar que el mes actual siempre este
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m")
    if now not in periodos:
        periodos.insert(0, now)
    return {"periodos": periodos}
