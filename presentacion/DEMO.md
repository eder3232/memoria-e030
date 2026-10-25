# Guion técnico de la demo

La presentación (`index.html`) ya contiene la salida real de cada paso, así que si la demo en
vivo falla puedes seguir con las diapositivas. Esta guía es para hacerla en vivo.

## Antes de subir al escenario

```sh
uv sync
git config core.hooksPath hooks
git switch main
uv run memoria --input input_example     # la primera compilación LaTeX tarda (caché de fuentes)
uv run pytest -q                         # 47 passed
```

- Abre `presentacion/index.html` en Chrome. **F** pantalla completa, **N** notas del orador,
  flechas o clic para avanzar. `#12` en la URL salta a la diapositiva 12.
- Deja una terminal abierta en la raíz del repo, con letra grande.
- Reemplaza la nota al pie del precio del cemento (diapositiva 5) por una fuente y fecha reales.

## 1. Todo en orden (main)

```sh
uv run pytest -q
uv run memoria --input input_example_porticos
```

Muestra el PDF: el paso del C/R dice `0.103 < 0.11 ⇒ (C/R) = 0.11`. La norma manda el mínimo.

## 2. El «ajuste» (rama demo/error-plantado)

```sh
git switch demo/error-plantado
git log -1 -p                 # el mensaje suena razonable; el diff quita el max(..., 0.11)
uv run pytest -q              # 5 failed: los nombres de las pruebas dicen qué se rompió
uv run memoria --input input_example_porticos --sin-pdf
                              # ERROR: el Excel no coincide con el motor → RECHAZADO
git blame -L 111,113 src/memoria_e030/norma/e030.py
                              # quién, cuándo y en qué commit
```

Punto a remarcar: el cortante bajó de 291.93 a 273.19 tonf (−6.4 %), del lado inseguro, y
**ninguna salida llegó a la entidad**.

## 3. BORRADOR (opcional)

```sh
git switch main
# cambia cualquier cosa en src/ sin hacer commit, por ejemplo un comentario
uv run memoria --input input_example     # el PDF sale con marca de agua BORRADOR
git restore src/
```

## 4. El hook (opcional)

```sh
mkdir input && cp input_example/proyecto.yaml input/
git add -f input/proyecto.yaml
git commit -m "avance"                   # ✋ Commit bloqueado
git restore --staged input/proyecto.yaml
```

## Después

```sh
git switch main
rm -rf input output
```

## Mantener la presentación al día

Los números, las fórmulas y las portadas de las diapositivas salen del motor:

```sh
uv run python presentacion/construir.py
```

Para repartir un PDF: en Chrome, Imprimir → Guardar como PDF, márgenes «Ninguno» y
«Gráficos de fondo» activado. Cada diapositiva sale en una página con todos sus fragmentos.
