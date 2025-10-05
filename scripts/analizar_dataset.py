#!/usr/bin/env python3
"""
Script para analizar el dataset de facturas e historias clínicas
y extraer patrones para mejorar el modelo de predicción de glosa.
"""

import json
import os
import pandas as pd
from pathlib import Path
import re
from collections import Counter

def analizar_dataset():
    """Analiza el dataset completo para extraer patrones"""
    
    base_path = Path("FEV_JSON-20250807T191037Z-1-001/FEV_JSON")
    
    # Contadores para análisis
    codigos_validacion = Counter()
    clases_validacion = Counter()
    descripciones = []
    observaciones = []
    
    # Archivos procesados
    archivos_procesados = 0
    errores_encontrados = 0
    
    print("Analizando dataset de validaciones...")
    
    for carpeta in base_path.iterdir():
        if carpeta.is_dir():
            print(f"Procesando: {carpeta.name}")
            
            # Buscar archivos JSON
            json_files = list(carpeta.glob("*.json"))
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    archivos_procesados += 1
                    
                    # Extraer información de validaciones
                    if 'ResultadosValidacion' in data:
                        for validacion in data['ResultadosValidacion']:
                            codigo = validacion.get('Codigo', '')
                            clase = validacion.get('Clase', '')
                            descripcion = validacion.get('Descripcion', '')
                            observacion = validacion.get('Observaciones', '')
                            
                            codigos_validacion[codigo] += 1
                            clases_validacion[clase] += 1
                            
                            if descripcion:
                                descripciones.append(descripcion)
                            if observacion:
                                observaciones.append(observacion)
                
                except Exception as e:
                    errores_encontrados += 1
                    print(f"Error procesando {json_file}: {e}")
    
    # Generar reporte
    print(f"\nRESUMEN DEL ANALISIS:")
    print(f"Archivos procesados: {archivos_procesados}")
    print(f"Errores encontrados: {errores_encontrados}")
    
    print(f"\nTOP 10 CODIGOS DE VALIDACION MAS FRECUENTES:")
    for codigo, count in codigos_validacion.most_common(10):
        print(f"  {codigo}: {count} veces")
    
    print(f"\nCLASES DE VALIDACION:")
    for clase, count in clases_validacion.most_common():
        print(f"  {clase}: {count} veces")
    
    # Guardar análisis detallado
    with open("analisis_dataset.json", "w", encoding="utf-8") as f:
        json.dump({
            "resumen": {
                "archivos_procesados": archivos_procesados,
                "errores_encontrados": errores_encontrados,
                "total_codigos": len(codigos_validacion),
                "total_clases": len(clases_validacion)
            },
            "codigos_validacion": dict(codigos_validacion),
            "clases_validacion": dict(clases_validacion),
            "descripciones_ejemplo": descripciones[:20],
            "observaciones_ejemplo": observaciones[:20]
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalisis guardado en: analisis_dataset.json")
    
    return {
        "codigos_validacion": codigos_validacion,
        "clases_validacion": clases_validacion,
        "descripciones": descripciones,
        "observaciones": observaciones
    }

if __name__ == "__main__":
    analizar_dataset()
