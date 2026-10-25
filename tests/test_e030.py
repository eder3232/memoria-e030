"""Pruebas de las funciones de la norma E.030.

Cada prueba con nombre de caso particular documenta una decisión: si alguien la
rompe meses después, el nombre explica qué se rompió y dónde está en la norma.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from memoria_e030.norma import e030

# --- Tablas: contra la transcripción de normas/E030-2018/ -------------------

def test_tabla1_factores_de_zona():
    assert e030.FACTOR_ZONA == {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}


@pytest.mark.parametrize("zona, suelo, S", [
    (4, "S2", 1.05), (3, "S2", 1.15), (2, "S3", 1.40), (1, "S3", 2.00), (1, "S0", 0.80),
])
def test_tabla3_factor_de_suelo(zona, suelo, S):
    assert e030.factor_suelo(zona, suelo) == S


def test_tabla3_suelo_S1_siempre_vale_uno():
    assert all(e030.FACTOR_SUELO[z]["S1"] == 1.00 for z in e030.FACTOR_SUELO)


@pytest.mark.parametrize("suelo, T_P, T_L", [
    ("S0", 0.3, 3.0), ("S1", 0.4, 2.5), ("S2", 0.6, 2.0), ("S3", 1.0, 1.6),
])
def test_tabla4_periodos(suelo, T_P, T_L):
    assert e030.periodos_suelo(suelo) == (T_P, T_L)


def test_tabla4_T_P_menor_que_T_L_en_todos_los_suelos():
    # Si alguien intercambia T_P y T_L al transcribir, esto falla
    assert all(tp < tl for tp, tl in e030.PERIODOS_SUELO.values())


# --- Factor C (Art. 14) -----------------------------------------------------

def test_C_en_la_plataforma_vale_2_5():
    assert e030.factor_amplificacion(0.2, 0.4, 2.5) == 2.5


def test_C_en_el_tramo_intermedio():
    assert e030.factor_amplificacion(0.8, 0.4, 2.5) == pytest.approx(1.25)


def test_C_en_el_tramo_de_desplazamiento_constante():
    assert e030.factor_amplificacion(3.0, 0.4, 2.5) == pytest.approx(2.5 * 0.4 * 2.5 / 9)


@pytest.mark.parametrize("suelo", list(e030.PERIODOS_SUELO))
def test_C_es_continuo_en_T_P_y_T_L(suelo):
    T_P, T_L = e030.periodos_suelo(suelo)
    for limite in (T_P, T_L):
        izq = e030.factor_amplificacion(limite - 1e-9, T_P, T_L)
        der = e030.factor_amplificacion(limite + 1e-9, T_P, T_L)
        assert izq == pytest.approx(der, rel=1e-6)


@given(
    suelo=st.sampled_from(list(e030.PERIODOS_SUELO)),
    T1=st.floats(0.01, 10), T2=st.floats(0.01, 10),
)
def test_C_nunca_crece_con_el_periodo(suelo, T1, T2):
    T_P, T_L = e030.periodos_suelo(suelo)
    a, b = sorted((T1, T2))
    assert e030.factor_amplificacion(b, T_P, T_L) <= e030.factor_amplificacion(a, T_P, T_L) + 1e-12


# --- C/R mínimo (Art. 28.2.1) -------------------------------------------------

def test_C_R_minimo_gobierna_en_edificio_flexible():
    # Pórticos de concreto (R = 8) con T = 1.8 s en suelo S1: C/R = 0.069 < 0.11
    C = e030.factor_amplificacion(1.8, 0.4, 2.5)
    assert C / 8 < 0.11
    assert e030.cociente_c_r(C, 8) == 0.11


def test_C_R_no_se_modifica_si_supera_el_minimo():
    assert e030.cociente_c_r(2.5, 6) == pytest.approx(2.5 / 6)


@given(C=st.floats(0.01, 2.5), R=st.floats(1, 8))
def test_C_R_de_diseno_nunca_es_menor_que_0_11(C, R):
    assert e030.cociente_c_r(C, R) >= 0.11


# --- Periodo, R, peso, k ------------------------------------------------------

def test_periodo_fundamental():
    assert e030.periodo_fundamental(13.8, 60) == pytest.approx(0.23)


def test_R_con_irregularidades():
    assert e030.coef_reduccion(8, 0.75, 0.9) == pytest.approx(5.4)


def test_peso_sismico_categoria_C_usa_25_por_ciento_de_CV():
    f = e030.fraccion_carga_viva("C", azotea=False)
    assert e030.peso_piso(270.0, 60.0, f) == pytest.approx(285.0)


def test_peso_sismico_categoria_A2_usa_50_por_ciento_de_CV():
    assert e030.fraccion_carga_viva("A2", azotea=False) == 0.50


def test_azotea_usa_25_por_ciento_aunque_la_categoria_sea_B():
    assert e030.fraccion_carga_viva("B", azotea=True) == 0.25


@pytest.mark.parametrize("T, k", [(0.3, 1.0), (0.5, 1.0), (1.0, 1.25), (2.5, 2.0), (4.0, 2.0)])
def test_exponente_k(T, k):
    assert e030.exponente_k(T) == pytest.approx(k)


# --- Distribución en altura (Art. 28.3) ---------------------------------------

@given(
    pesos=st.lists(st.floats(10, 1000), min_size=1, max_size=30),
    k=st.floats(1.0, 2.0),
    V=st.floats(1, 5000),
)
def test_la_suma_de_fuerzas_es_el_cortante_basal(pesos, k, V):
    alturas = [3.0 * (i + 1) for i in range(len(pesos))]
    alfas, fuerzas = e030.distribucion_fuerzas(pesos, alturas, k, V)
    assert sum(alfas) == pytest.approx(1.0)
    assert sum(fuerzas) == pytest.approx(V)
