"""Lectura y validación de una carpeta de entrada (`input/` o `input_example/`).

Esta es la frontera entre el motor (público) y los datos del proyecto
(confidenciales). El motor nunca lee nada que no pase por aquí.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

from .norma import e030

ARCHIVO = "proyecto.yaml"


class EntradaInvalida(ValueError):
    pass


@dataclass(frozen=True)
class Especialista:
    rol: str
    nombre: str
    cip: str


@dataclass(frozen=True)
class Proyecto:
    """Metadatos: lo que hace confidencial a una memoria. No interviene en el cálculo."""
    nombre: str
    ubicacion: str
    entidad: str
    contratista: str
    especialistas: tuple[Especialista, ...]
    fecha: str


@dataclass(frozen=True)
class Parametros:
    zona: int
    suelo: str
    categoria: str
    sistema: str
    I_a: float
    I_p: float
    C_T: int


@dataclass(frozen=True)
class Piso:
    nivel: int
    h: float          # altura de entrepiso (m)
    CM: float         # carga muerta (tonf)
    CV: float         # carga viva (tonf)
    azotea: bool


@dataclass(frozen=True)
class Entrada:
    carpeta: Path
    proyecto: Proyecto
    parametros: Parametros
    pisos: tuple[Piso, ...]


def _opcion(valor, permitidos, campo):
    if valor not in permitidos:
        opciones = ", ".join(str(p) for p in permitidos)
        raise EntradaInvalida(f"'{campo}' = {valor!r} no es válido. Opciones: {opciones}")
    return valor


def _positivo(valor, campo):
    if not isinstance(valor, (int, float)) or valor <= 0:
        raise EntradaInvalida(f"'{campo}' debe ser un número positivo (se recibió {valor!r})")
    return float(valor)


def _irregularidad(valor, campo):
    valor = _positivo(valor, campo)
    if valor > 1.0:
        raise EntradaInvalida(f"'{campo}' debe estar entre 0 y 1 (Art. 20); se recibió {valor}")
    return valor


def leer(carpeta: str | Path) -> Entrada:
    carpeta = Path(carpeta)
    archivo = carpeta / ARCHIVO
    if not archivo.exists():
        raise EntradaInvalida(f"No existe {archivo}")
    datos = yaml.safe_load(archivo.read_text(encoding="utf-8"))

    try:
        p = datos["proyecto"]
        proyecto = Proyecto(
            nombre=p["nombre"],
            ubicacion=p["ubicacion"],
            entidad=p["entidad"],
            contratista=p["contratista"],
            especialistas=tuple(
                Especialista(e["rol"], e["nombre"], str(e["cip"])) for e in p["especialistas"]
            ),
            fecha=str(p["fecha"]),
        )

        q = datos["parametros"]
        parametros = Parametros(
            zona=_opcion(q["zona"], e030.FACTOR_ZONA, "parametros.zona"),
            suelo=_opcion(q["suelo"], e030.PERIODOS_SUELO, "parametros.suelo"),
            categoria=_opcion(q["categoria"], e030.FACTOR_USO, "parametros.categoria"),
            sistema=_opcion(q["sistema"], e030.COEF_R0, "parametros.sistema"),
            I_a=_irregularidad(q.get("I_a", 1.0), "parametros.I_a"),
            I_p=_irregularidad(q.get("I_p", 1.0), "parametros.I_p"),
            C_T=_opcion(q["C_T"], e030.VALORES_CT, "parametros.C_T"),
        )

        pisos = tuple(
            Piso(
                nivel=int(x["nivel"]),
                h=_positivo(x["h"], f"pisos[{i}].h"),
                CM=_positivo(x["CM"], f"pisos[{i}].CM"),
                CV=float(x.get("CV", 0.0)),
                azotea=bool(x.get("azotea", False)),
            )
            for i, x in enumerate(datos["pisos"])
        )
    except KeyError as falta:
        raise EntradaInvalida(f"Falta el campo {falta} en {archivo}") from None

    if not pisos:
        raise EntradaInvalida("Debe haber al menos un piso")
    if [x.nivel for x in pisos] != list(range(1, len(pisos) + 1)):
        raise EntradaInvalida("Los pisos deben listarse de abajo hacia arriba: nivel 1, 2, 3...")

    return Entrada(carpeta, proyecto, parametros, pisos)
