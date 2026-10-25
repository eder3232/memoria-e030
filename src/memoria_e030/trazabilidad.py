"""Sello de trazabilidad: de qué versión exacta del código salió un entregable."""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Trazabilidad:
    commit: str | None
    con_cambios: bool    # hay código modificado sin commit: el entregable es un borrador
    fecha: str

    @property
    def es_borrador(self) -> bool:
        return self.commit is None or self.con_cambios

    @property
    def version(self) -> str:
        if self.commit is None:
            return "sin control de versiones"
        return self.commit + (" (+ cambios sin commit)" if self.con_cambios else "")

    @property
    def estado(self) -> str:
        return "BORRADOR — no usar para presentar" if self.es_borrador else "Versión registrada"


def _git(*args) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return r.stdout.strip()


def obtener() -> Trazabilidad:
    commit = _git("rev-parse", "--short", "HEAD")
    # Solo cuenta el código que produce el cálculo, no los datos ni las salidas
    cambios = _git("status", "--porcelain", "--", "src", "pyproject.toml", "uv.lock")
    return Trazabilidad(
        commit=commit,
        con_cambios=bool(cambios),
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
