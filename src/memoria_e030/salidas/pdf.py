"""Memoria A4 en PDF, para revisión: fórmula, sustitución y resultado de cada paso.

Las derivaciones salen de aplicar handcalcs a las MISMAS funciones del motor
(`norma/e030.py`), no a copias. Además se comprueba que el valor que handcalcs
imprime sea el mismo que calculó el motor: lo impreso es lo calculado.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from handcalcs.decorator import handcalc
from jinja2 import Environment, FileSystemLoader

from ..calculo import Resultado
from ..entrada import Entrada
from ..norma import e030
from ..trazabilidad import Trazabilidad

PLANTILLAS = Path(__file__).parent / "plantillas"

# Ajustes de notación sobre lo que produce handcalcs
REEMPLAZOS = {
    r"\text{Since, }": r"\text{Como }",
    r"\lt": "<",   # handcalcs apunta a MathJax; LaTeX no define \lt ni \gt
    r"\gt": ">",
    "C_{R}": r"\left(\frac{C}{R}\right)",
    r"\mathrm{CM}": r"\mathit{CM}",
    r"\mathrm{CV}": r"\mathit{CV}",
}


def _derivacion(funcion, *args, esperado):
    latex, valor = handcalc(jupyter_display=False, precision=3)(funcion)(*args)
    if abs(valor - esperado) > 1e-9 * max(1.0, abs(esperado)):
        raise AssertionError(f"handcalcs de {funcion.__name__} dio {valor}, el motor {esperado}")
    latex = latex.strip().removeprefix("$$").removesuffix("$$").strip()
    for viejo, nuevo in REEMPLAZOS.items():
        latex = latex.replace(viejo, nuevo)
    # handcalcs alinea también el resultado final ("&= 6.000") y deja un hueco
    lineas = [l[::-1].replace("=&", "=", 1)[::-1] if l.count("&=") == 2 else l for l in latex.splitlines()]
    return "\n".join(lineas)


def _tabla(texto):
    return rf"\begin{{aligned}} {texto} \end{{aligned}}"


def _f(x, d=3):
    return f"{x:.{d}f}"


def construir_pasos(entrada: Entrada, r: Resultado) -> list[dict]:
    q = entrada.parametros
    piso = entrada.pisos[0]
    fila = r.pisos[0]
    ec_c_r = (
        rf"\frac{{C}}{{R}} = \frac{{{_f(r.C)}}}{{{_f(r.R)}}} = {_f(r.C_R_calculado)}"
        + (rf" < {e030.C_R_MINIMO} \;\Rightarrow\; \left(\frac{{C}}{{R}}\right) = {e030.C_R_MINIMO}"
           if r.gobierna_minimo_c_r else
           rf" \geq {e030.C_R_MINIMO} \;\Rightarrow\; \left(\frac{{C}}{{R}}\right) = {_f(r.C_R)}")
    )
    return [
        {"seccion": "Parámetros de sitio"},
        {"titulo": "Factor de zona", "ref": "Art. 10, Tabla N° 1",
         "texto": f"La edificación se ubica en la zona sísmica {q.zona}.",
         "latex": _tabla(rf"Z &= {r.Z:.2f}")},
        {"titulo": "Factor de suelo", "ref": "Art. 13.1, Tabla N° 3",
         "texto": f"Perfil de suelo {q.suelo} en zona {q.zona}.",
         "latex": _tabla(rf"S &= {r.S:.2f}")},
        {"titulo": "Periodos del suelo", "ref": "Art. 13.2, Tabla N° 4",
         "texto": f"Para el perfil {q.suelo}:",
         "latex": _tabla(rf"T_{{P}} &= {r.T_P:.1f}\ \mathrm{{s}} & T_{{L}} &= {r.T_L:.1f}\ \mathrm{{s}}")},

        {"seccion": "Edificación y sistema estructural"},
        {"titulo": "Factor de uso", "ref": "Art. 15, Tabla N° 5",
         "texto": f"Categoría {q.categoria}.",
         "latex": _tabla(rf"U &= {r.U:.1f}")},
        {"titulo": "Coeficiente básico de reducción", "ref": "Art. 18, Tabla N° 7",
         "texto": f"Sistema estructural: {q.sistema.replace('_', ' ')}.",
         "latex": _tabla(rf"R_{{0}} &= {r.R_0:g}")},
        {"titulo": "Coeficiente de reducción de fuerzas sísmicas", "ref": "Art. 22",
         "texto": "Con los factores de irregularidad en altura y en planta (Art. 20):",
         "latex": _derivacion(e030.coef_reduccion, r.R_0, q.I_a, q.I_p, esperado=r.R)},

        {"seccion": "Periodo y amplificación sísmica"},
        {"titulo": "Periodo fundamental de vibración", "ref": "Art. 28.4.1",
         "texto": f"Altura total $h_{{n}} = {_f(r.h_n, 2)}$ m y $C_{{T}} = {q.C_T}$.",
         "latex": _derivacion(e030.periodo_fundamental, r.h_n, q.C_T, esperado=r.T)},
        {"titulo": "Factor de amplificación sísmica", "ref": "Art. 14",
         "texto": "El tramo aplicable depende de $T$ frente a $T_{P}$ y $T_{L}$.",
         "latex": _derivacion(e030.factor_amplificacion, r.T, r.T_P, r.T_L, esperado=r.C)},
        {"titulo": "Cociente C/R", "ref": "Art. 28.2.1",
         "texto": f"El valor de C/R no debe considerarse menor que {e030.C_R_MINIMO}.",
         "latex": _tabla(ec_c_r.replace("=", "&=", 1))},

        {"seccion": "Peso sísmico y fuerza cortante en la base"},
        {"titulo": "Peso sísmico por nivel", "ref": "Art. 26",
         "texto": (f"Se suma la carga muerta y una fracción $f$ de la carga viva. "
                   f"Ejemplo para el nivel {piso.nivel}; el resto en la tabla de distribución."),
         "latex": _derivacion(e030.peso_piso, piso.CM, piso.CV, fila.f, esperado=fila.P_i)},
        {"titulo": "Peso sísmico total", "ref": "Art. 26",
         "texto": "Suma de los pesos de todos los niveles:",
         "latex": _tabla(rf"P &= \sum P_{{i}} = {_f(r.P, 2)}\ \mathrm{{tonf}}")},
        {"titulo": "Fuerza cortante en la base", "ref": "Art. 28.2.1",
         "texto": "",
         "latex": _derivacion(e030.cortante_basal, r.Z, r.U, r.S, r.C_R, r.P, esperado=r.V),
         "destacar": rf"\mathbf{{V = {_f(r.V, 2)}}}\ \mathrm{{tonf}} \qquad \text{{({100 * r.V / r.P:.2f}\,\% de $P$)}}"},

        {"seccion": "Distribución de fuerzas en altura"},
        {"titulo": "Exponente $k$", "ref": "Art. 28.3.2",
         "texto": "Depende del periodo fundamental $T$.",
         "latex": _derivacion(e030.exponente_k, r.T, esperado=r.k)},
        {"titulo": "Fuerza en cada nivel", "ref": "Art. 28.3.1",
         "texto": "",
         "latex": r"F_{i} = \alpha_{i} \cdot V \qquad \alpha_{i} = \frac{P_{i}\,h_{i}^{k}}{\sum_{j=1}^{n} P_{j}\,h_{j}^{k}}",
         "tabla_pisos": True},
    ]


def _escapar(texto) -> str:
    texto = str(texto)
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        texto = texto.replace(a, b)
    return texto


def renderizar_tex(entrada: Entrada, r: Resultado, traza: Trazabilidad, verificacion: str) -> str:
    env = Environment(
        loader=FileSystemLoader(PLANTILLAS),
        block_start_string="((*", block_end_string="*))",
        variable_start_string="(((", variable_end_string=")))",
        comment_start_string="((#", comment_end_string="#))",
        trim_blocks=True, lstrip_blocks=True, autoescape=False,
    )
    env.filters["e"] = _escapar
    env.filters["f"] = _f
    return env.get_template("memoria.tex.j2").render(
        p=entrada.proyecto, q=entrada.parametros, pisos=entrada.pisos, r=r, traza=traza,
        pasos=construir_pasos(entrada, r), norma=e030.NORMA, verificacion=verificacion,
    )


def compilar(entrada: Entrada, r: Resultado, traza: Trazabilidad, destino: Path, verificacion: str):
    if shutil.which("latexmk") is None:
        raise RuntimeError("No se encontró latexmk. Instala TeX Live o MiKTeX, o usa --sin-pdf.")
    tex = renderizar_tex(entrada, r, traza, verificacion)
    with tempfile.TemporaryDirectory() as tmp:
        fuente = Path(tmp) / "memoria.tex"
        fuente.write_text(tex, encoding="utf-8")
        proceso = subprocess.run(
            ["latexmk", "-lualatex", "-interaction=nonstopmode", "-halt-on-error", fuente.name],
            cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proceso.returncode != 0:
            log = (Path(tmp) / "memoria.log")
            detalle = log.read_text(encoding="utf-8", errors="replace")[-3000:] if log.exists() else proceso.stdout[-3000:]
            raise RuntimeError(f"Falló la compilación LaTeX:\n{detalle}")
        shutil.copy(Path(tmp) / "memoria.pdf", destino)
        shutil.copy(fuente, destino.with_suffix(".tex"))
