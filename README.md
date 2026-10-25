# Memoria de cálculo E.030 — piloto

Análisis sísmico estático según la Norma Técnica **E.030-2018** (RNE, Perú), construido como un
proyecto de software: con control de versiones, pruebas y trazabilidad hasta el artículo de la norma.

El entregable sigue siendo un **Excel con fórmulas vivas**, porque eso piden las entidades.
La diferencia está en cómo se produce:

```
normas/ ──► funciones puras ──► pruebas
                  │
   input/ (privado) o input_example/ (público)
                  │
          ┌───────┴────────┐
          ▼                ▼
   Excel con fórmulas   Memoria A4 (PDF)
   para la entidad      para revisión
          │
          └─► se recalcula y se compara contra Python: si no coincide, no se entrega
```

## Uso

```sh
uv sync
git config core.hooksPath hooks       # una vez por clon: activa la protección de datos
uv run memoria --input input_example  # caso público de ejemplo
uv run memoria --input input          # tu proyecto real (carpeta ignorada por git)
uv run pytest                         # pruebas
```

Salida en `output/<carpeta>/`: `memoria_e030.xlsx` y `memoria_e030.pdf`.
El PDF necesita LaTeX (TeX Live o MiKTeX con `latexmk` y `lualatex`); sin él usa `--sin-pdf`.

## El motor es público; los datos, no

La razón para no compartir un Excel casi nunca es el cálculo: son los **datos**. La entidad, la
empresa, los nombres y colegiaturas de los especialistas, los precios. Este proyecto los separa:

| Carpeta | Contenido | ¿Se sube a GitHub? |
|---|---|---|
| `src/` | El motor: funciones de la norma y generadores | Sí |
| `tests/` | Pruebas | Sí |
| `normas/` | Transcripción y estado de verificación | Sí (los PDF con copyright, no) |
| `input_example/` | Un proyecto **ficticio** completo | Sí |
| `input/` | Tu proyecto real | **No**: `.gitignore` + hook |
| `output/` | Los entregables generados (contienen los datos reales) | **No**: `.gitignore` + hook |

El hook `hooks/pre-commit` bloquea incluso un `git add -f input/...`: lo que entra al historial de
git se queda ahí aunque luego se borre. El generador también limpia los metadatos del Excel (el
autor del archivo es `memoria-e030`, nunca tu usuario de Windows).

Para empezar un proyecto real: copia `input_example/proyecto.yaml` a `input/proyecto.yaml` y edítalo.

## Por qué dos salidas

- **Excel**: lo exigen municipalidades, gobiernos regionales y otras entidades. Usa nombres definidos,
  así la celda dice `=Z*U*C_R*S*P` y no `=B3*B4*B7*B5*B12`. Las tablas de la norma están dentro
  del libro, de modo que también las búsquedas son fórmulas.
- **Memoria A4**: para revisarte a ti mismo o pedirle ayuda a un colega. Cada paso muestra la
  descripción, el artículo, la fórmula, la fórmula con números y el resultado. Revisar esto toma
  minutos; seguirle la pista a cada celda de un Excel, horas.

## Garantías

1. **Lo impreso es lo calculado.** Las derivaciones del PDF salen de aplicar
   [handcalcs](https://github.com/connorferster/handcalcs) a las mismas funciones de
   `src/memoria_e030/norma/e030.py`, y se comprueba que el valor que imprime coincida con el del motor.
2. **El Excel coincide con el motor.** Tras generarlo se recalcula con la librería `formulas` (Python
   puro, sin Excel) y se comparan todos los valores. Si uno difiere, el archivo se renombra a
   `RECHAZADO` y no se genera la memoria. La prueba `test_la_verificacion_detecta_una_formula_alterada`
   planta un error a propósito para demostrar que se detecta.
3. **Cada entregable dice de qué versión salió.** La portada lleva el commit. Si el código tiene cambios
   sin commit, el PDF sale con la marca de agua **BORRADOR**.
4. **Cada caso particular es una prueba con nombre.** Por ejemplo,
   `test_azotea_usa_25_por_ciento_aunque_la_categoria_sea_B`. Si alguien lo rompe meses después,
   la prueba falla y su nombre explica qué se rompió.

## Decisiones técnicas

- **Sin `LAMBDA` en Excel**: requiere Excel 365/2024 y muchas entidades usan 2016/2019.
- **`C_amp` y `R_coef`**: Excel reserva los nombres `C` y `R` (notación F1C1).
- **Nombres de variables como en la norma** (`T_P`, `R_0`, `I_a`): handcalcs los convierte en la
  notación impresa (T<sub>P</sub>, R<sub>0</sub>, I<sub>a</sub>).
- **Unidades**: tonf, m, s, documentadas en cada módulo. Un sistema de unidades explícito
  (`forallpeople` o `pint`) es una mejora pendiente.

## Alcance y advertencias

- Solo el **análisis estático** (Art. 28). No incluye análisis dinámico modal espectral, derivas ni
  verificación de irregularidades: `I_a` e `I_p` se ingresan como datos.
- Categorías A2, B y C; un subconjunto de sistemas estructurales.
- **Las tablas transcritas en `normas/E030-2018/` aún deben verificarse contra el PDF oficial.**
  Mira la tabla de estado en ese README.
- La herramienta no reemplaza el criterio ni la firma del ingeniero responsable.

## Presentación

`presentacion/index.html` es la charla que acompaña este piloto: HTML sin dependencias externas
(KaTeX va incluido en `vendor/`), funciona sin internet. Los números, fórmulas y portadas salen del
motor con `uv run python presentacion/construir.py`. La demo en vivo usa la rama
`demo/error-plantado`; el paso a paso está en `presentacion/DEMO.md`.

## Estructura

```
src/memoria_e030/
  norma/e030.py          funciones puras y tablas, cada una con su artículo
  entrada.py             lectura y validación de proyecto.yaml (frontera público/privado)
  calculo.py             orquesta el análisis; solo números
  salidas/excel.py       compilador a Excel con fórmulas vivas
  salidas/pdf.py         memoria A4 con handcalcs + LaTeX
  verificacion.py        recalcula el Excel y lo compara con el motor
  trazabilidad.py        commit y estado del código
  cli.py                 uv run memoria
normas/E030-2018/        transcripción y estado de verificación
input_example/           proyecto ficticio, público
input_example_porticos/  torre flexible donde gobierna C/R ≥ 0.11 (caso de la demo)
presentacion/            la charla (HTML) y el guion de la demo
hooks/pre-commit         bloquea input/ y output/
tests/
```
