# E.030 Diseño Sismorresistente — versión 2018

**Fuente oficial:** Reglamento Nacional de Edificaciones, Norma Técnica E.030, modificada por
R.M. N° 355-2018-VIVIENDA. El PDF oficial se descarga del Ministerio de Vivienda / El Peruano.
Guárdalo en esta carpeta como `E030-2018.pdf` (está en `.gitignore`: el repo solo cita).

**La fuente de verdad es el PDF oficial, no este markdown.** Este archivo es una transcripción
de trabajo de las partes que usa el motor, para que cada número de `src/memoria_e030/norma/e030.py`
se pueda rastrear hasta su tabla.

## Estado de verificación

Cada tabla debe revisarla una persona contra el PDF oficial antes de usar el motor en un proyecto
real. Marca la casilla en un commit propio, con tu nombre en el mensaje.

| Elemento | Artículo | Usado en | Verificado contra PDF |
|---|---|---|---|
| Tabla N° 1, factor Z | Art. 10 | `FACTOR_ZONA` | ☐ pendiente |
| Tabla N° 3, factor S | Art. 13.1 | `FACTOR_SUELO` | ☐ pendiente |
| Tabla N° 4, T_P y T_L | Art. 13.2 | `PERIODOS_SUELO` | ☐ pendiente |
| Factor C por tramos | Art. 14 | `factor_amplificacion` | ☐ pendiente |
| Tabla N° 5, factor U | Art. 15 | `FACTOR_USO` | ☐ pendiente |
| Tabla N° 7, R_0 (subconjunto) | Art. 18 | `COEF_R0` | ☐ pendiente |
| R = R_0 · I_a · I_p | Art. 22 | `coef_reduccion` | ☐ pendiente |
| Peso sísmico, fracción de CV | Art. 26 | `FRACCION_CV` | ☐ pendiente |
| V = ZUCS/R · P y C/R ≥ 0,11 | Art. 28.2.1 | `cortante_basal`, `cociente_c_r` | ☐ pendiente |
| Exponente k | Art. 28.3.2 | `exponente_k` | ☐ pendiente |
| T = h_n / C_T | Art. 28.4.1 | `periodo_fundamental` | ☐ pendiente |

Los números de artículo también deben confirmarse: si la norma se actualiza, la numeración puede
cambiar y las citas de la memoria quedarían mal.

## Transcripción

### Tabla N° 1 — Factores de zona

| Zona | Z |
|---|---|
| 4 | 0,45 |
| 3 | 0,35 |
| 2 | 0,25 |
| 1 | 0,10 |

### Tabla N° 3 — Factor de suelo S

| Zona \ Suelo | S0 | S1 | S2 | S3 |
|---|---|---|---|---|
| Z4 | 0,80 | 1,00 | 1,05 | 1,10 |
| Z3 | 0,80 | 1,00 | 1,15 | 1,20 |
| Z2 | 0,80 | 1,00 | 1,20 | 1,40 |
| Z1 | 0,80 | 1,00 | 1,60 | 2,00 |

### Tabla N° 4 — Periodos T_P y T_L

| | S0 | S1 | S2 | S3 |
|---|---|---|---|---|
| T_P (s) | 0,3 | 0,4 | 0,6 | 1,0 |
| T_L (s) | 3,0 | 2,5 | 2,0 | 1,6 |

### Art. 14 — Factor de amplificación sísmica C

| Rango | C |
|---|---|
| T < T_P | 2,5 |
| T_P < T < T_L | 2,5 · (T_P / T) |
| T > T_L | 2,5 · (T_P · T_L / T²) |

### Tabla N° 5 — Factor de uso U (subconjunto del piloto)

| Categoría | U |
|---|---|
| A2 Edificaciones esenciales | 1,5 |
| B Edificaciones importantes | 1,3 |
| C Edificaciones comunes | 1,0 |

A1 (aislamiento sísmico obligatorio en zonas 3 y 4) y D (criterio del proyectista) quedan fuera del piloto.

### Tabla N° 7 — Coeficiente básico de reducción R_0 (subconjunto del piloto)

| Sistema estructural | R_0 |
|---|---|
| Concreto armado: pórticos | 8 |
| Concreto armado: dual | 7 |
| Concreto armado: muros estructurales | 6 |
| Concreto armado: muros de ductilidad limitada | 4 |
| Albañilería armada o confinada | 3 |

### Art. 26 — Peso sísmico P

Se calcula sumando a la carga permanente un porcentaje de la carga viva:

- Categorías A y B: 50 % de la carga viva.
- Categoría C: 25 % de la carga viva.
- Azoteas y techos en general: 25 % de la carga viva.

### Art. 28.2.1 — Fuerza cortante en la base

V = Z · U · C · S / R · P, y el valor de C/R no debe considerarse menor que 0,11.

### Art. 28.3.2 — Exponente k

- T ≤ 0,5 s: k = 1,0
- T > 0,5 s: k = (0,75 + 0,5 · T) ≤ 2,0

### Art. 28.4.1 — Periodo fundamental

T = h_n / C_T, con C_T = 35, 45 o 60 según el sistema estructural.
