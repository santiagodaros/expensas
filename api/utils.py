"""Helpers de saneo compartidos entre routers que escriben archivos en disco
(reportes.py, finanzas.py) a partir de datos provistos por el usuario."""
import re
import sqlite3
from fastapi import HTTPException


def safe_filename_part(s: str) -> str:
    """Sanea un fragmento para uso en nombre de archivo: sin separadores de path,
    sin secuencias de traversal, sin caracteres de control."""
    s = str(s or "")
    s = s.replace("/", "_").replace("\\", "_")
    s = re.sub(r"\.\.+", "_", s)
    s = re.sub(r"[\x00-\x1f\x7f]", "", s)
    s = s.strip(" .")
    return s or "sin_nombre"


_PERIODO_RE = re.compile(r"^\d{4}-\d{2}$")


def safe_periodo(periodo: str) -> str:
    """El periodo suele llegar como segmento de URL y se usa directo como
    nombre de carpeta; validamos el formato esperado (YYYY-MM)."""
    if not _PERIODO_RE.match(periodo or ""):
        raise HTTPException(400, detail="Periodo inválido, formato esperado YYYY-MM")
    return periodo


def load_pagos_periodo(db: sqlite3.Connection, consorcio_id: int, periodo: str):
    """Para cada unidad del consorcio, devuelve (pagos_periodo_anterior, pagos_periodo_actual).

    El 'periodo anterior' es el ultimo pago registrado con periodo < periodo actual,
    no necesariamente el mes calendario inmediatamente anterior: si un mes se salteo
    sin registrar nada (ni siquiera con pagado=0), la mora o el saldo a favor arrastrado
    de meses anteriores debe seguir viéndose, en vez de resetearse a cero.
    """
    uid_list = [u["id"] for u in db.execute(
        "SELECT id FROM unidades WHERE consorcio_id=?", (consorcio_id,)
    ).fetchall()]
    if not uid_list:
        return {}, {}
    ph = ",".join("?" * len(uid_list))
    act_rows = db.execute(
        f"SELECT * FROM pagos WHERE periodo=? AND unidad_id IN ({ph})",
        [periodo] + uid_list
    ).fetchall()
    ant_rows = db.execute(
        f"""SELECT p.* FROM pagos p
            INNER JOIN (
                SELECT unidad_id, MAX(periodo) AS max_periodo
                FROM pagos WHERE periodo < ? AND unidad_id IN ({ph})
                GROUP BY unidad_id
            ) m ON p.unidad_id = m.unidad_id AND p.periodo = m.max_periodo""",
        [periodo] + uid_list
    ).fetchall()
    p_act = {p["unidad_id"]: dict(p) for p in act_rows}
    p_ant = {p["unidad_id"]: dict(p) for p in ant_rows}
    return p_ant, p_act


def apply_interes_mora(saldo_ant: float, interes_pct: float) -> float:
    """Aplica interes punitorio mensual sobre una deuda arrastrada de un periodo
    anterior ya registrado. Nunca se aplica a saldos a favor (negativos) ni al
    saldo de apertura de una unidad nueva (todavia no paso ningun periodo desde
    que se cargo, asi que no hay atraso que penalizar)."""
    if saldo_ant > 0 and interes_pct > 0:
        return round(saldo_ant * (1 + interes_pct / 100.0), 2)
    return saldo_ant
