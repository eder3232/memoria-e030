"""El Excel debe coincidir con el motor, y no debe filtrar datos personales."""

import getpass
import shutil
import subprocess
import zipfile
from pathlib import Path

import openpyxl
import pytest

from memoria_e030 import calculo, entrada, trazabilidad, verificacion
from memoria_e030.salidas import excel, pdf

RAIZ = Path(__file__).resolve().parents[1]


def _generar(tmp_path, carpeta="input_example", cambios=None):
    if cambios:
        texto = (RAIZ / carpeta / "proyecto.yaml").read_text(encoding="utf-8")
        for viejo, nuevo in cambios.items():
            texto = texto.replace(viejo, nuevo)
        (tmp_path / "in").mkdir()
        (tmp_path / "in" / "proyecto.yaml").write_text(texto, encoding="utf-8")
        carpeta = tmp_path / "in"
    datos = entrada.leer(RAIZ / carpeta if isinstance(carpeta, str) else carpeta)
    r = calculo.calcular(datos)
    ruta = tmp_path / "memoria.xlsx"
    mapa = excel.compilar(datos, r, trazabilidad.obtener(), ruta)
    return datos, r, ruta, mapa


def test_excel_coincide_con_el_motor(tmp_path):
    _, r, ruta, mapa = _generar(tmp_path)
    assert verificacion.verificar(ruta, r, mapa) == []


def test_excel_coincide_cuando_gobierna_el_minimo_C_R(tmp_path):
    # Edificio de pórticos alto: activa el tramo de C y el mínimo de C/R
    _, r, ruta, mapa = _generar(tmp_path, cambios={
        "sistema: concreto_muros": "sistema: concreto_porticos",
        "C_T: 60": "C_T: 35",
        "h: 2.70": "h: 12.0",
    })
    assert r.gobierna_minimo_c_r
    assert verificacion.verificar(ruta, r, mapa) == []


def test_la_verificacion_detecta_una_formula_alterada(tmp_path):
    """El error de la demo: alguien quita el MAX(...; 0.11) del Excel a mano."""
    _, r, ruta, mapa = _generar(tmp_path, cambios={
        "sistema: concreto_muros": "sistema: concreto_porticos",
        "C_T: 60": "C_T: 35",
        "h: 2.70": "h: 12.0",
    })
    wb = openpyxl.load_workbook(ruta)
    hoja, celda = mapa.memoria["C_R"].split("!")
    wb[hoja][celda] = "=C_R_calc"
    wb.save(ruta)

    diferencias = verificacion.verificar(ruta, r, mapa)
    celdas = {d.celda for d in diferencias}
    assert mapa.memoria["C_R"] in celdas
    assert mapa.memoria["V"] in celdas


def test_excel_no_contiene_el_usuario_del_sistema(tmp_path):
    *_, ruta, _ = _generar(tmp_path)
    with zipfile.ZipFile(ruta) as z:
        propiedades = z.read("docProps/core.xml").decode("utf-8")
    assert getpass.getuser() not in propiedades
    assert "memoria-e030" in propiedades


def test_handcalcs_imprime_lo_que_calcula_el_motor(tmp_path):
    datos, r, *_ = _generar(tmp_path)
    # construir_pasos lanza AssertionError si handcalcs y el motor difieren
    pasos = pdf.construir_pasos(datos, r)
    assert any("V &=" in p.get("latex", "") for p in pasos)


@pytest.mark.skipif(shutil.which("git") is None, reason="requiere git")
@pytest.mark.parametrize("ruta", ["input/proyecto.yaml", "output/x/memoria_e030.xlsx"])
def test_datos_reales_y_salidas_estan_ignorados_por_git(ruta):
    r = subprocess.run(["git", "check-ignore", "-q", ruta], cwd=RAIZ)
    if r.returncode == 128:
        pytest.skip("no es un repositorio git")
    assert r.returncode == 0, f"{ruta} no está en .gitignore"


def test_input_example_no_esta_ignorado():
    r = subprocess.run(["git", "check-ignore", "-q", "input_example/proyecto.yaml"], cwd=RAIZ)
    if r.returncode == 128:
        pytest.skip("no es un repositorio git")
    assert r.returncode == 1
