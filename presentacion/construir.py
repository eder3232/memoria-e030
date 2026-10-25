"""Genera los recursos de la presentación desde el motor, no a mano.

    uv run python presentacion/construir.py

- recursos/memoria.js: valores y derivaciones LaTeX (las mismas de la memoria A4)
- recursos/portada_registrada.png y portada_borrador.png

Si el motor cambia, se vuelve a correr y las diapositivas quedan al día.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

from memoria_e030 import calculo, entrada, trazabilidad
from memoria_e030.norma import e030
from memoria_e030.salidas import pdf

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
RECURSOS = AQUI / "recursos"


def _portada(datos, r, traza, destino: Path):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "memoria.pdf"
        pdf.compilar(datos, r, traza, ruta, "OK, 45 valores coinciden")
        subprocess.run(["pdftoppm", "-r", "110", "-f", "1", "-l", "1", "-singlefile", "-png",
                        str(ruta), str(destino.with_suffix(""))], check=True)


def main():
    RECURSOS.mkdir(exist_ok=True)
    datos = entrada.leer(RAIZ / "input_example")
    r = calculo.calcular(datos)
    pasos = {p["titulo"]: p["latex"] for p in pdf.construir_pasos(datos, r) if "latex" in p}

    torre = calculo.calcular(entrada.leer(RAIZ / "input_example_porticos"))
    # El error de la demo: usar C/R sin el mínimo de 0.11
    V_sin_minimo = e030.cortante_basal(torre.Z, torre.U, torre.S, torre.C_R_calculado, torre.P)

    traza = trazabilidad.obtener()
    datos_js = {
        "commit": traza.commit,
        "ejemplo": {k: getattr(r, k) for k in ("Z", "U", "S", "C", "R", "T", "C_R", "P", "V")},
        "pasos": {
            "V": pasos["Fuerza cortante en la base"],
            "C": pasos["Factor de amplificación sísmica"],
            "T": pasos["Periodo fundamental de vibración"],
        },
        "torre": {"C_R_calculado": torre.C_R_calculado, "V": torre.V, "V_sin_minimo": V_sin_minimo},
    }
    (RECURSOS / "memoria.js").write_text(
        "// Generado por presentacion/construir.py. No editar a mano.\n"
        f"window.MEMORIA = {json.dumps(datos_js, ensure_ascii=False, indent=2)};\n",
        encoding="utf-8",
    )

    if shutil.which("pdftoppm") and shutil.which("latexmk"):
        registrada = replace(traza, con_cambios=False) if traza.commit else traza
        _portada(datos, r, registrada, RECURSOS / "portada_registrada.png")
        _portada(datos, r, replace(registrada, con_cambios=True), RECURSOS / "portada_borrador.png")
    else:
        print("Sin pdftoppm/latexmk: no se regeneraron las portadas.", file=sys.stderr)
    print(f"Recursos generados en {RECURSOS}")


if __name__ == "__main__":
    main()
