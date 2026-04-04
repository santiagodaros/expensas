"""Router: Proveedores"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import sqlite3
from api.database import get_db, rows_to_list, row_to_dict
from api.schemas import ProveedorOut, ProveedorCreate, ProveedorUpdate, CuentaCorrienteRow, MessageOut

router = APIRouter(tags=["Proveedores"])


@router.get("/proveedores", response_model=List[ProveedorOut])
def list_proveedores(consorcio: int = Query(...), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM proveedores WHERE consorcio_id=? ORDER BY razon_social",
        (consorcio,)
    ).fetchall()
    return rows_to_list(rows)


@router.post("/proveedores", response_model=ProveedorOut, status_code=201)
def create_proveedor(consorcio_id: int, body: ProveedorCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO proveedores(consorcio_id,razon_social,cuit,domicilio,cat_afip,cbu) VALUES(?,?,?,?,?,?)",
        (consorcio_id, body.razon_social, body.cuit, body.domicilio, body.cat_afip, body.cbu)
    )
    row = db.execute("SELECT * FROM proveedores WHERE id=?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)


@router.put("/proveedores/{pid}", response_model=ProveedorOut)
def update_proveedor(pid: int, body: ProveedorUpdate, db: sqlite3.Connection = Depends(get_db)):
    db.execute(
        "UPDATE proveedores SET razon_social=?,cuit=?,domicilio=?,cat_afip=?,cbu=? WHERE id=?",
        (body.razon_social, body.cuit, body.domicilio, body.cat_afip, body.cbu, pid)
    )
    row = db.execute("SELECT * FROM proveedores WHERE id=?", (pid,)).fetchone()
    if not row:
        raise HTTPException(404, "Proveedor no encontrado")
    return row_to_dict(row)


@router.delete("/proveedores/{pid}", response_model=MessageOut)
def delete_proveedor(pid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM proveedores WHERE id=?", (pid,))
    return {"ok": True, "message": f"Proveedor {pid} eliminado"}


@router.get("/proveedores/resumen", response_model=List[CuentaCorrienteRow])
def resumen_proveedores(consorcio: int = Query(...), db: sqlite3.Connection = Depends(get_db)):
    """Total facturado por proveedor en el consorcio."""
    rows = db.execute(
        """SELECT p.id as proveedor_id, p.razon_social,
                  COALESCE(SUM(g.monto),0) as total_gastos,
                  COUNT(DISTINCT g.periodo) as periodos
           FROM proveedores p
           LEFT JOIN gastos g ON g.proveedor_id=p.id
           WHERE p.consorcio_id=?
           GROUP BY p.id ORDER BY total_gastos DESC""",
        (consorcio,)
    ).fetchall()
    return rows_to_list(rows)


@router.get("/proveedores/{pid}/cuenta_corriente", response_model=List[dict])
def cuenta_corriente(pid: int, db: sqlite3.Connection = Depends(get_db)):
    """Gastos asociados a este proveedor, agrupados por periodo."""
    rows = db.execute(
        """SELECT periodo, SUM(monto) as total, COUNT(*) as qty
           FROM gastos WHERE proveedor_id=?
           GROUP BY periodo ORDER BY periodo DESC""",
        (pid,)
    ).fetchall()
    return rows_to_list(rows)
