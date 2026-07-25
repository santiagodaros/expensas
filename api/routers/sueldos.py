"""Router: Sueldos y Cargas Sociales"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import sqlite3
from api.database import get_db, rows_to_list, row_to_dict
from api.schemas import SueldoOut, SueldoCreate, SueldoUpdate, MessageOut

router = APIRouter(tags=["Sueldos"])


def _total(body: SueldoCreate | SueldoUpdate) -> float:
    return body.sueldo_bruto + body.cargas_suterh + body.cargas_fateryh + body.otras_cargas


def _gasto_descripcion(empleado: str, concepto: str) -> str:
    return f"Sueldo: {empleado} ({concepto})"


@router.get("/sueldos", response_model=List[SueldoOut])
def list_sueldos(
    consorcio: int = Query(...),
    periodo: str = Query(...),
    db: sqlite3.Connection = Depends(get_db),
):
    rows = db.execute(
        "SELECT * FROM sueldos WHERE consorcio_id=? AND periodo=? ORDER BY empleado",
        (consorcio, periodo),
    ).fetchall()
    return rows_to_list(rows)


@router.get("/sueldos/historial", response_model=List[SueldoOut])
def historial_empleado(
    consorcio: int = Query(...),
    empleado: str = Query(...),
    db: sqlite3.Connection = Depends(get_db),
):
    """Todos los recibos de un empleado en este consorcio, a través de todos los
    períodos (para comparar su sueldo mes a mes, no solo el período actual)."""
    rows = db.execute(
        "SELECT * FROM sueldos WHERE consorcio_id=? AND empleado=? ORDER BY periodo DESC",
        (consorcio, empleado),
    ).fetchall()
    return rows_to_list(rows)


@router.post("/sueldos", response_model=SueldoOut, status_code=201)
def create_sueldo(
    consorcio_id: int = Query(...),
    periodo: str = Query(...),
    body: SueldoCreate = ...,
    db: sqlite3.Connection = Depends(get_db),
):
    total = _total(body)

    # 1. Crear el gasto ordinario correspondiente
    cur_g = db.execute(
        "INSERT INTO gastos(consorcio_id, periodo, categoria, descripcion, monto, tipo) VALUES(?,?,?,?,?,?)",
        (consorcio_id, periodo, "A", _gasto_descripcion(body.empleado, body.concepto), total, "ordinario"),
    )
    gasto_id = cur_g.lastrowid

    # 2. Crear el registro de sueldo vinculado al gasto
    cur_s = db.execute(
        """INSERT INTO sueldos(consorcio_id, periodo, empleado, concepto,
                               sueldo_bruto, cargas_suterh, cargas_fateryh, otras_cargas,
                               total_gasto, gasto_id)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (consorcio_id, periodo, body.empleado, body.concepto,
         body.sueldo_bruto, body.cargas_suterh, body.cargas_fateryh, body.otras_cargas,
         total, gasto_id),
    )
    row = db.execute("SELECT * FROM sueldos WHERE id=?", (cur_s.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.put("/sueldos/{sid}", response_model=SueldoOut)
def update_sueldo(
    sid: int,
    body: SueldoUpdate,
    db: sqlite3.Connection = Depends(get_db),
):
    sueldo = db.execute("SELECT * FROM sueldos WHERE id=?", (sid,)).fetchone()
    if not sueldo:
        raise HTTPException(404, "Sueldo no encontrado")

    total = _total(body)

    # 1. Actualizar gasto vinculado si existe
    if sueldo["gasto_id"]:
        db.execute(
            "UPDATE gastos SET descripcion=?, monto=? WHERE id=?",
            (_gasto_descripcion(body.empleado, body.concepto), total, sueldo["gasto_id"]),
        )

    # 2. Actualizar sueldo
    db.execute(
        """UPDATE sueldos SET empleado=?, concepto=?, sueldo_bruto=?, cargas_suterh=?,
                              cargas_fateryh=?, otras_cargas=?, total_gasto=?
           WHERE id=?""",
        (body.empleado, body.concepto, body.sueldo_bruto, body.cargas_suterh,
         body.cargas_fateryh, body.otras_cargas, total, sid),
    )
    row = db.execute("SELECT * FROM sueldos WHERE id=?", (sid,)).fetchone()
    return row_to_dict(row)


@router.delete("/sueldos/{sid}", response_model=MessageOut)
def delete_sueldo(sid: int, db: sqlite3.Connection = Depends(get_db)):
    sueldo = db.execute("SELECT gasto_id FROM sueldos WHERE id=?", (sid,)).fetchone()
    if not sueldo:
        raise HTTPException(404, "Sueldo no encontrado")

    # 1. Eliminar el gasto vinculado
    if sueldo["gasto_id"]:
        db.execute("DELETE FROM gastos WHERE id=?", (sueldo["gasto_id"],))

    # 2. Eliminar el sueldo
    db.execute("DELETE FROM sueldos WHERE id=?", (sid,))
    return {"ok": True, "message": f"Sueldo {sid} eliminado"}
