"""uv run memoria --input input_example/

Un origen, varias salidas: el mismo cálculo genera el Excel (para la entidad)
y la memoria A4 (para revisión). El Excel se recalcula y se compara contra el
motor antes de entregar nada.
"""

import argparse
import sys
from pathlib import Path

from . import calculo, entrada, trazabilidad, verificacion
from .salidas import excel, pdf


def main(argv=None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="memoria", description="Memoria de cálculo E.030 — análisis estático")
    ap.add_argument("--input", required=True, help="carpeta con proyecto.yaml (input/ o input_example/)")
    ap.add_argument("--output", default="output", help="carpeta de salida (por defecto output/, ignorada por git)")
    ap.add_argument("--sin-pdf", action="store_true", help="no generar la memoria A4")
    args = ap.parse_args(argv)

    try:
        datos = entrada.leer(args.input)
    except entrada.EntradaInvalida as error:
        print(f"Entrada inválida: {error}", file=sys.stderr)
        return 2

    resultado = calculo.calcular(datos)
    traza = trazabilidad.obtener()
    destino = Path(args.output) / datos.carpeta.resolve().name
    destino.mkdir(parents=True, exist_ok=True)

    print(f"Proyecto: {datos.proyecto.nombre}")
    print(f"  T = {resultado.T:.3f} s   C = {resultado.C:.3f}   C/R = {resultado.C_R:.3f}"
          + ("  (gobierna el mínimo 0.11)" if resultado.gobierna_minimo_c_r else ""))
    print(f"  P = {resultado.P:.2f} tonf   V = {resultado.V:.2f} tonf")

    ruta_excel = destino / "memoria_e030.xlsx"
    mapa = excel.compilar(datos, resultado, traza, ruta_excel)
    diferencias = verificacion.verificar(ruta_excel, resultado, mapa)
    if diferencias:
        rechazado = ruta_excel.with_name("memoria_e030.RECHAZADO.xlsx")
        ruta_excel.replace(rechazado)
        print(f"\nERROR: el Excel no coincide con el motor en {len(diferencias)} celdas:", file=sys.stderr)
        for d in diferencias:
            print(f"  {d.celda}: Excel={d.excel}  Python={d.python}", file=sys.stderr)
        print(f"Se guardó como {rechazado} para inspección. No se generó la memoria.", file=sys.stderr)
        return 1
    n = len(mapa.memoria) + sum(len(c) for c in mapa.pisos.values())
    estado = f"OK, {n} valores coinciden"
    print(f"  Excel:  {ruta_excel}  (verificación {estado})")

    if not args.sin_pdf:
        ruta_pdf = destino / "memoria_e030.pdf"
        pdf.compilar(datos, resultado, traza, ruta_pdf, estado)
        print(f"  PDF:    {ruta_pdf}")

    if traza.es_borrador:
        print(f"\nAviso: {traza.estado} (versión {traza.version}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
