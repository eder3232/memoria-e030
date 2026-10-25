"""Norma Técnica E.030 "Diseño Sismorresistente" (RNE), versión 2018.

Regla del módulo: solo funciones puras y tablas. Nada de archivos, nada de
Excel, nada del proyecto. Cada función cita el artículo o tabla de origen; la
transcripción de esas tablas está en `normas/E030-2018/`.

Los nombres de variables imitan la notación de la norma (T_P, R_0, I_a...)
porque handcalcs los convierte en la notación impresa de la memoria.

Unidades: fuerzas y pesos en tonf, longitudes en m, periodos en s.
"""

NORMA = "E.030-2018"

# Tabla N° 1 (Art. 10) — Factores de zona Z
FACTOR_ZONA = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}

# Tabla N° 3 (Art. 13.1) — Factor de suelo S, por zona y perfil de suelo
FACTOR_SUELO = {
    4: {"S0": 0.80, "S1": 1.00, "S2": 1.05, "S3": 1.10},
    3: {"S0": 0.80, "S1": 1.00, "S2": 1.15, "S3": 1.20},
    2: {"S0": 0.80, "S1": 1.00, "S2": 1.20, "S3": 1.40},
    1: {"S0": 0.80, "S1": 1.00, "S2": 1.60, "S3": 2.00},
}

# Tabla N° 4 (Art. 13.2) — Periodos T_P y T_L (s), por perfil de suelo
PERIODOS_SUELO = {
    "S0": (0.3, 3.0),
    "S1": (0.4, 2.5),
    "S2": (0.6, 2.0),
    "S3": (1.0, 1.6),
}

# Tabla N° 5 (Art. 15) — Factor de uso U.
# A1 (aislamiento obligatorio en zonas 3 y 4) y D (criterio del proyectista)
# quedan fuera del alcance de este piloto a propósito.
FACTOR_USO = {"A2": 1.5, "B": 1.3, "C": 1.0}

# Tabla N° 7 (Art. 18) — Coeficiente básico de reducción R_0 (subconjunto)
COEF_R0 = {
    "concreto_porticos": 8,
    "concreto_dual": 7,
    "concreto_muros": 6,
    "concreto_muros_ductilidad_limitada": 4,
    "albanileria_armada_o_confinada": 3,
}

# Art. 28.4.1 — Valores admisibles de C_T
VALORES_CT = (35, 45, 60)

# Art. 26 — Fracción de carga viva que se suma al peso sísmico
FRACCION_CV = {"A": 0.50, "B": 0.50, "C": 0.25}
FRACCION_CV_AZOTEA = 0.25

# Art. 28.2.1 — "El valor de C/R no deberá considerarse menor que 0,11"
C_R_MINIMO = 0.11


def factor_zona(zona: int) -> float:
    """Z. Art. 10, Tabla N° 1."""
    return FACTOR_ZONA[zona]


def factor_suelo(zona: int, suelo: str) -> float:
    """S. Art. 13.1, Tabla N° 3."""
    return FACTOR_SUELO[zona][suelo]


def periodos_suelo(suelo: str) -> tuple[float, float]:
    """(T_P, T_L). Art. 13.2, Tabla N° 4."""
    return PERIODOS_SUELO[suelo]


def factor_uso(categoria: str) -> float:
    """U. Art. 15, Tabla N° 5."""
    return FACTOR_USO[categoria]


def coef_basico_reduccion(sistema: str) -> float:
    """R_0. Art. 18, Tabla N° 7."""
    return COEF_R0[sistema]


def fraccion_carga_viva(categoria: str, azotea: bool) -> float:
    """Fracción de CV para el peso sísmico. Art. 26 (literales a, b, c, e)."""
    if azotea:
        return FRACCION_CV_AZOTEA
    return FRACCION_CV[categoria[0]]


def coef_reduccion(R_0, I_a, I_p):
    """R = R_0 · I_a · I_p. Art. 22."""
    R = R_0 * I_a * I_p
    return R


def periodo_fundamental(h_n, C_T):
    """T = h_n / C_T. Art. 28.4.1."""
    T = h_n / C_T
    return T


def factor_amplificacion(T, T_P, T_L):
    """C. Art. 14."""
    if T < T_P: C = 2.5
    elif T < T_L: C = 2.5 * (T_P / T)
    else: C = 2.5 * (T_P * T_L / T**2)
    return C


def cociente_c_r(C, R):
    """C/R de diseño, con el mínimo de 0,11. Art. 28.2.1."""
    return max(C / R, C_R_MINIMO)


def peso_piso(CM, CV, f):
    """P_i = CM + f · CV. Art. 26."""
    P_i = CM + f * CV
    return P_i


def cortante_basal(Z, U, S, C_R, P):
    """V = Z · U · (C/R) · S · P. Art. 28.2.1."""
    V = Z * U * C_R * S * P
    return V


def exponente_k(T):
    """Exponente de distribución en altura. Art. 28.3.2."""
    if T <= 0.5: k = 1.0
    else: k = min(0.75 + 0.5 * T, 2.0)
    return k


def distribucion_fuerzas(pesos, alturas, k, V):
    """Fuerzas laterales F_i = α_i · V, α_i = P_i h_i^k / Σ P_j h_j^k. Art. 28.3.

    `alturas` son las alturas de cada nivel medidas desde la base.
    Devuelve (lista de α_i, lista de F_i), en el mismo orden de entrada.
    """
    productos = [p * h**k for p, h in zip(pesos, alturas)]
    total = sum(productos)
    alfas = [x / total for x in productos]
    return alfas, [a * V for a in alfas]
