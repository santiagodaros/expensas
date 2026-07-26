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
from api.schemas import ConsorcioOut, ConsorcioCreate, UnidadOut, UnidadCreate, MessageOut, UnidadBatchIn, UnidadBatchOut

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
        "INSERT INTO consorcios(nombre,cuit,direccion,unidades,reserva_pct,dia_vto,interes_mora_pct) VALUES(?,?,?,?,?,?,?)",
        (body.nombre, body.cuit, body.direccion, body.unidades, body.reserva_pct, body.dia_vto, body.interes_mora_pct)
    )
    row = db.execute("SELECT * FROM consorcios WHERE id=?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.put("/consorcios/{cid}", response_model=ConsorcioOut)
def update_consorcio(cid: int, body: ConsorcioCreate, db: sqlite3.Connection = Depends(get_db)):
    db.execute(
        "UPDATE consorcios SET nombre=?,cuit=?,direccion=?,unidades=?,reserva_pct=?,dia_vto=?,interes_mora_pct=? WHERE id=?",
        (body.nombre, body.cuit, body.direccion, body.unidades, body.reserva_pct, body.dia_vto, body.interes_mora_pct, cid)
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

def _tiene_pagos(db: sqlite3.Connection, uid: int) -> bool:
    return db.execute("SELECT 1 FROM pagos WHERE unidad_id=? LIMIT 1", (uid,)).fetchone() is not None


def _with_saldo_editable(db: sqlite3.Connection, rows: list) -> list:
    """El saldo de apertura solo es editable mientras la unidad no tenga
    ningun pago registrado; una vez que arranco a operar, el arrastre real
    de deuda/credito viene del historial de pagos, no de este valor manual.
    Una sola consulta batcheada en vez de una por unidad (evita N+1 al listar)."""
    out = [dict(row) for row in rows]
    ids = [d["id"] for d in out]
    if not ids:
        return out
    ph = ",".join("?" * len(ids))
    con_pagos = {r["unidad_id"] for r in db.execute(
        f"SELECT DISTINCT unidad_id FROM pagos WHERE unidad_id IN ({ph})", ids
    ).fetchall()}
    for d in out:
        d["saldo_apertura_editable"] = d["id"] not in con_pagos
    return out


@router.get("/consorcios/{cid}/unidades", response_model=List[UnidadOut])
def list_unidades(cid: int, db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)",
        (cid,)
    ).fetchall()
    return _with_saldo_editable(db, rows)


@router.post("/consorcios/{cid}/unidades", response_model=UnidadOut, status_code=201)
def create_unidad(cid: int, body: UnidadCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO unidades(consorcio_id,unidad,piso,dpto,propietario,inquilino,coef_a,coef_b,coef_c,email,saldo_apertura) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (cid, body.unidad, body.piso, body.dpto, body.propietario,
         body.inquilino, body.coef_a, body.coef_b, body.coef_c, body.email, body.saldo_apertura)
    )
    row = db.execute("SELECT * FROM unidades WHERE id=?", (cur.lastrowid,)).fetchone()
    return _with_saldo_editable(db, [row])[0]


@router.put("/unidades/{uid}", response_model=UnidadOut)
def update_unidad(uid: int, body: UnidadCreate, db: sqlite3.Connection = Depends(get_db)):
    existe = db.execute("SELECT saldo_apertura FROM unidades WHERE id=?", (uid,)).fetchone()
    if not existe:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    # Si la unidad ya tiene pagos registrados, el saldo de apertura queda
    # bloqueado: se ignora lo que venga en el body y se conserva el valor
    # historico, para no permitir reescribir el arrastre despues de operar.
    saldo_apertura = body.saldo_apertura if not _tiene_pagos(db, uid) else existe["saldo_apertura"]
    db.execute(
        "UPDATE unidades SET unidad=?,piso=?,dpto=?,propietario=?,inquilino=?,coef_a=?,coef_b=?,coef_c=?,email=?,saldo_apertura=? WHERE id=?",
        (body.unidad, body.piso, body.dpto, body.propietario,
         body.inquilino, body.coef_a, body.coef_b, body.coef_c, body.email, saldo_apertura, uid)
    )
    row = db.execute("SELECT * FROM unidades WHERE id=?", (uid,)).fetchone()
    return _with_saldo_editable(db, [row])[0]


@router.delete("/unidades/{uid}", response_model=MessageOut)
def delete_unidad(uid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM unidades WHERE id=?", (uid,))
    return {"ok": True, "message": f"Unidad {uid} eliminada"}


@router.post("/consorcios/{cid}/unidades/batch", response_model=UnidadBatchOut, status_code=200)
def batch_upsert_unidades(cid: int, body: UnidadBatchIn, db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM unidades WHERE consorcio_id=?", (cid,)).fetchall()
    existentes: dict = {row_to_dict(r)["unidad"]: row_to_dict(r) for r in rows}

    insertados = 0
    actualizados = 0
    sin_cambios = 0

    for u in body.unidades:
        # Normalizar strings vacíos a None para comparación consistente con la DB
        prop = u.propietario or None
        inq = u.inquilino or None
        email = u.email or None

        if u.unidad in existentes:
            ex = existentes[u.unidad]
            # El saldo de apertura solo se re-importa si la unidad todavia no
            # tiene pagos registrados (mismo lock que en el alta/edicion manual).
            editable = not _tiene_pagos(db, ex["id"])
            nuevo_saldo = u.saldo_apertura if editable else ex["saldo_apertura"]
            changed = (
                ex["piso"] != u.piso
                or ex["dpto"] != u.dpto
                or ex["propietario"] != prop
                or ex["inquilino"] != inq
                or abs((ex["coef_a"] or 0.0) - u.coef_a) > 1e-6
                or abs((ex["coef_b"] or 0.0) - u.coef_b) > 1e-6
                or abs((ex["coef_c"] or 0.0) - u.coef_c) > 1e-6
                or ex["email"] != email
                or (editable and abs((ex["saldo_apertura"] or 0.0) - u.saldo_apertura) > 1e-6)
            )
            if changed:
                db.execute(
                    "UPDATE unidades SET piso=?,dpto=?,propietario=?,inquilino=?,coef_a=?,coef_b=?,coef_c=?,email=?,saldo_apertura=? "
                    "WHERE consorcio_id=? AND unidad=?",
                    (u.piso, u.dpto, prop, inq, u.coef_a, u.coef_b, u.coef_c, email, nuevo_saldo, cid, u.unidad)
                )
                actualizados += 1
            else:
                sin_cambios += 1
        else:
            db.execute(
                "INSERT INTO unidades(consorcio_id,unidad,piso,dpto,propietario,inquilino,coef_a,coef_b,coef_c,email,saldo_apertura) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (cid, u.unidad, u.piso, u.dpto, prop, inq, u.coef_a, u.coef_b, u.coef_c, email, u.saldo_apertura)
            )
            insertados += 1

    return {
        "ok": True,
        "message": f"Importación completa: {insertados} nuevas, {actualizados} actualizadas, {sin_cambios} sin cambios.",
        "insertados": insertados,
        "actualizados": actualizados,
        "sin_cambios": sin_cambios,
    }


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
