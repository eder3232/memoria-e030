"""Análisis sísmico estático (E.030 Art. 28) a partir de una Entrada.

Solo números: aquí no hay Excel, LaTeX ni archivos. Las salidas (PDF y Excel)
leen este Resultado; ninguna recalcula por su cuenta.
"""

from dataclasses import dataclass
from itertools import accumulate

from .entrada import Entrada
from .norma import e030


@dataclass(frozen=True)
class FilaPiso:
    nivel: int
    h_i: float        # altura del nivel desde la base (m)
    f: float          # fracción de CV usada
    P_i: float        # peso sísmico del nivel (tonf)
    alfa: float
    F_i: float        # fuerza lateral (tonf)
    V_i: float        # cortante de entrepiso (tonf)


@dataclass(frozen=True)
class Resultado:
    Z: float
    S: float
    T_P: float
    T_L: float
    U: float
    R_0: float
    R: float
    h_n: float
    T: float
    C: float
    C_R_calculado: float
    C_R: float
    P: float
    V: float
    k: float
    pisos: tuple[FilaPiso, ...]

    @property
    def gobierna_minimo_c_r(self) -> bool:
        return self.C_R_calculado < e030.C_R_MINIMO


def calcular(entrada: Entrada) -> Resultado:
    q = entrada.parametros

    Z = e030.factor_zona(q.zona)
    S = e030.factor_suelo(q.zona, q.suelo)
    T_P, T_L = e030.periodos_suelo(q.suelo)
    U = e030.factor_uso(q.categoria)
    R_0 = e030.coef_basico_reduccion(q.sistema)
    R = e030.coef_reduccion(R_0, q.I_a, q.I_p)

    alturas = list(accumulate(p.h for p in entrada.pisos))
    h_n = alturas[-1]
    T = e030.periodo_fundamental(h_n, q.C_T)
    C = e030.factor_amplificacion(T, T_P, T_L)
    C_R = e030.cociente_c_r(C, R)

    fracciones = [e030.fraccion_carga_viva(q.categoria, p.azotea) for p in entrada.pisos]
    pesos = [e030.peso_piso(p.CM, p.CV, f) for p, f in zip(entrada.pisos, fracciones)]
    P = sum(pesos)

    V = e030.cortante_basal(Z, U, S, C_R, P)
    k = e030.exponente_k(T)
    alfas, fuerzas = e030.distribucion_fuerzas(pesos, alturas, k, V)
    # Cortante de entrepiso: suma de las fuerzas desde el nivel hacia arriba
    cortantes = list(accumulate(reversed(fuerzas)))[::-1]

    pisos = tuple(
        FilaPiso(p.nivel, h, f, P_i, a, F_i, V_i)
        for p, h, f, P_i, a, F_i, V_i in zip(entrada.pisos, alturas, fracciones, pesos, alfas, fuerzas, cortantes)
    )
    return Resultado(Z, S, T_P, T_L, U, R_0, R, h_n, T, C, C / R, C_R, P, V, k, pisos)
