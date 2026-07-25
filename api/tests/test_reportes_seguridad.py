"""
Tests de los helpers de saneo compartidos (api/utils.py), usados por
reportes.py y finanzas.py para prevenir path traversal al escribir archivos
derivados de datos del usuario (nombre de consorcio, propietario, comprobantes).

No se testea por HTTP: los endpoints de /reportes escriben PDFs reales en
~/Documents/Expensas/Boletas y llaman a os.startfile(), efectos de sistema que
no queremos disparar en un test. Se testean los helpers puros directamente.
"""
import pytest
from fastapi import HTTPException
from api.utils import safe_filename_part, safe_periodo


def test_safe_filename_part_neutraliza_separadores_de_path():
    assert "/" not in safe_filename_part("../../etc/passwd")
    assert "\\" not in safe_filename_part("..\\..\\Windows\\System32\\evil")


def test_safe_filename_part_neutraliza_secuencias_de_traversal():
    result = safe_filename_part("nombre..con..puntos")
    assert ".." not in result


def test_safe_filename_part_nombre_normal_no_se_altera_de_mas():
    assert safe_filename_part("Juan Perez") == "Juan Perez"


def test_safe_filename_part_vacio_devuelve_fallback():
    assert safe_filename_part("") == "sin_nombre"
    assert safe_filename_part(None) == "sin_nombre"


def test_safe_periodo_acepta_formato_valido():
    assert safe_periodo("2026-07") == "2026-07"


def test_safe_periodo_rechaza_path_traversal():
    with pytest.raises(HTTPException) as exc:
        safe_periodo("../../../Windows")
    assert exc.value.status_code == 400


def test_safe_periodo_rechaza_formato_invalido():
    with pytest.raises(HTTPException):
        safe_periodo("julio-2026")
