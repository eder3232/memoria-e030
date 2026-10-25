"""El caso de input_example comparado contra un cálculo hecho a mano."""

import pytest

from memoria_e030 import calculo, entrada


@pytest.fixture(scope="module")
def resultado():
    return calculo.calcular(entrada.leer("input_example"))


def test_caso_ejemplo_contra_calculo_manual(resultado):
    # Zona 4, S1, categoría C, muros de concreto, h_n = 13.80 m, C_T = 60
    # T = 13.80/60 = 0.23 s < T_P = 0.4  ->  C = 2.5 ;  C/R = 2.5/6 = 0.4167
    # P = (285+0.25·60) + 3·(270+0.25·60) + (230+0.25·30) = 1392.50 tonf
    # V = 0.45 · 1.0 · 0.4167 · 1.0 · 1392.50 = 261.09 tonf
    assert resultado.T == pytest.approx(0.23)
    assert resultado.C == 2.5
    assert resultado.P == pytest.approx(1392.50)
    assert resultado.V == pytest.approx(261.09375)
    assert not resultado.gobierna_minimo_c_r


def test_torre_de_porticos_gobierna_el_minimo_C_R():
    # h_n = 3.5 + 13·3.0 = 42.5 m ; T = 42.5/35 = 1.214 s ; C = 2.5·0.4/1.214 = 0.824
    # C/R = 0.824/8 = 0.103 < 0.11  ->  se diseña con 0.11
    r = calculo.calcular(entrada.leer("input_example_porticos"))
    assert r.C_R_calculado == pytest.approx(0.1029, abs=1e-4)
    assert r.gobierna_minimo_c_r
    assert r.V == pytest.approx(0.45 * 1.0 * 0.11 * 1.0 * r.P)


def test_cortante_de_entrepiso_del_primer_nivel_es_V(resultado):
    assert resultado.pisos[0].V_i == pytest.approx(resultado.V)


def test_entrada_rechaza_zona_inexistente(tmp_path):
    texto = open("input_example/proyecto.yaml", encoding="utf-8").read().replace("zona: 4 ", "zona: 5 ")
    (tmp_path / "proyecto.yaml").write_text(texto, encoding="utf-8")
    with pytest.raises(entrada.EntradaInvalida, match="zona"):
        entrada.leer(tmp_path)


def test_entrada_rechaza_irregularidad_mayor_que_uno(tmp_path):
    texto = open("input_example/proyecto.yaml", encoding="utf-8").read().replace("I_a: 1.0", "I_a: 1.2")
    (tmp_path / "proyecto.yaml").write_text(texto, encoding="utf-8")
    with pytest.raises(entrada.EntradaInvalida, match="I_a"):
        entrada.leer(tmp_path)
