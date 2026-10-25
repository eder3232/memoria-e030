"""Verificación cruzada: recalcula el Excel generado y lo compara con el motor.

El Excel tiene sus propias fórmulas, así que podría divergir del Python. Esta
verificación lo impide: si algún valor no coincide, el entregable no sale.
Usa la librería `formulas` (Python puro), así funciona sin Excel ni LibreOffice.
"""

import re
import warnings
from dataclasses import dataclass
from pathlib import Path

from .calculo import Resultado
from .salidas.excel import MapaCeldas

TOLERANCIA = 1e-9


@dataclass(frozen=True)
class Diferencia:
    celda: str
    excel: float | None
    python: float


def _recalcular(ruta: Path) -> dict[str, float]:
    import formulas  # importación lenta: solo cuando se verifica

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo = formulas.ExcelModel().loads(str(ruta)).finish()
        solucion = modelo.calculate()
    valores = {}
    for clave, rango in solucion.items():
        # "'[memoria.xlsx]MEMORIA'!F5" -> "MEMORIA!F5"
        m = re.fullmatch(r"'\[[^\]]+\](.+)'!([A-Z]+\d+)", clave)
        if m:
            valor = rango.value[0][0]
            if isinstance(valor, (int, float)):
                valores[f"{m[1]}!{m[2]}".upper()] = float(valor)
    return valores


def verificar(ruta: Path, resultado: Resultado, mapa: MapaCeldas) -> list[Diferencia]:
    excel = _recalcular(ruta)
    esperados = [(celda, getattr(resultado, attr)) for attr, celda in mapa.memoria.items()]
    for attr, celdas in mapa.pisos.items():
        esperados += [(c, getattr(fila, attr)) for c, fila in zip(celdas, resultado.pisos)]

    diferencias = []
    for celda, python in esperados:
        valor = excel.get(celda.upper())
        if valor is None or abs(valor - python) > TOLERANCIA * max(1.0, abs(python)):
            diferencias.append(Diferencia(celda, valor, python))
    return diferencias
