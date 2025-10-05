#!/usr/bin/env python3
"""
Script simplificado para generar reporte de métricas sin emojis
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import pandas as pd

def generar_reporte_simple():
    """Genera reporte simple de las métricas"""
    
    # Cargar análisis
    with open("analisis_dataset.json", "r", encoding="utf-8") as f:
        datos = json.load(f)
    
    print("\n" + "="*60)
    print("REPORTE DETALLADO DE METRICAS DEL DATASET")
    print("="*60)
    
    print(f"\nDATOS GENERALES:")
    print(f"   • Archivos procesados: {datos['resumen']['archivos_procesados']}")
    print(f"   • Total validaciones: {sum(datos['codigos_validacion'].values())}")
    print(f"   • Errores encontrados: {datos['resumen']['errores_encontrados']}")
    
    print(f"\nTOP 5 CODIGOS MAS PROBLEMATICOS:")
    codigos_ordenados = sorted(datos['codigos_validacion'].items(), key=lambda x: x[1], reverse=True)
    for i, (codigo, count) in enumerate(codigos_ordenados[:5], 1):
        print(f"   {i}. {codigo}: {count} ocurrencias")
    
    print(f"\nANALISIS DE RIESGO:")
    codigos_riesgo = {
        'RVC033': ('CIE no valido', 'ALTO'),
        'RVG19': ('Validacion PSS/PTS', 'ALTO'),
        'RVC019': ('CUPS validacion', 'MEDIO'),
        'RVC051': ('Finalidad', 'MEDIO'),
        'RVC065': ('Otros', 'BAJO')
    }
    
    alto_riesgo = 0
    medio_riesgo = 0
    bajo_riesgo = 0
    
    for codigo, (descripcion, riesgo) in codigos_riesgo.items():
        if codigo in datos['codigos_validacion']:
            count = datos['codigos_validacion'][codigo]
            print(f"   • {codigo} ({descripcion}): {count} veces - RIESGO {riesgo}")
            
            if riesgo == 'ALTO':
                alto_riesgo += count
            elif riesgo == 'MEDIO':
                medio_riesgo += count
            else:
                bajo_riesgo += count
    
    total = sum(datos['codigos_validacion'].values())
    
    print(f"\nDISTRIBUCION DE RIESGO:")
    print(f"   • ALTO RIESGO: {alto_riesgo} validaciones ({alto_riesgo/total*100:.1f}%)")
    print(f"   • MEDIO RIESGO: {medio_riesgo} validaciones ({medio_riesgo/total*100:.1f}%)")
    print(f"   • BAJO RIESGO: {bajo_riesgo} validaciones ({bajo_riesgo/total*100:.1f}%)")
    
    print(f"\nRECOMENDACIONES PARA EL MODELO:")
    print(f"   1. Priorizar codigos RVC033 y RVG19 (alto riesgo de glosa)")
    print(f"   2. Mejorar deteccion de codigos CIE invalidos")
    print(f"   3. Validar coherencia entre CUPS y diagnosticos")
    print(f"   4. Revisar validaciones PSS/PTS")
    print(f"   5. Implementar pesos especificos por codigo de riesgo")
    
    print(f"\nMETRICAS PARA ENTRENAMIENTO:")
    print(f"   • Probabilidad base de glosa: {(alto_riesgo/total)*100:.1f}%")
    print(f"   • Codigos de alto riesgo: {alto_riesgo}/{total} ({(alto_riesgo/total)*100:.1f}%)")
    print(f"   • Datos suficientes para entrenamiento: {'SI' if datos['resumen']['archivos_procesados'] >= 10 else 'NO'}")
    
    # Crear gráfico simple
    try:
        plt.figure(figsize=(12, 8))
        
        # Gráfico 1: Códigos más frecuentes
        plt.subplot(2, 2, 1)
        codigos_top = dict(codigos_ordenados[:8])
        plt.bar(codigos_top.keys(), codigos_top.values(), color='skyblue')
        plt.title('Codigos de Validacion Mas Frecuentes')
        plt.xlabel('Codigo')
        plt.ylabel('Frecuencia')
        plt.xticks(rotation=45)
        
        # Gráfico 2: Distribución de riesgo
        plt.subplot(2, 2, 2)
        niveles = ['ALTO', 'MEDIO', 'BAJO']
        valores = [alto_riesgo, medio_riesgo, bajo_riesgo]
        colores = ['red', 'orange', 'green']
        plt.bar(niveles, valores, color=colores, alpha=0.7)
        plt.title('Distribucion por Nivel de Riesgo')
        plt.xlabel('Nivel de Riesgo')
        plt.ylabel('Cantidad')
        
        # Gráfico 3: Porcentajes
        plt.subplot(2, 2, 3)
        porcentajes = [alto_riesgo/total*100, medio_riesgo/total*100, bajo_riesgo/total*100]
        plt.pie(porcentajes, labels=niveles, autopct='%1.1f%%', colors=colores)
        plt.title('Distribucion Porcentual de Riesgo')
        
        # Gráfico 4: Resumen
        plt.subplot(2, 2, 4)
        plt.axis('off')
        resumen_texto = f"""RESUMEN ESTADISTICO
        
Archivos: {datos['resumen']['archivos_procesados']}
Validaciones: {total}
Errores: {datos['resumen']['errores_encontrados']}

Codigo mas frecuente:
{max(datos['codigos_validacion'].items(), key=lambda x: x[1])[0]}: {max(datos['codigos_validacion'].values())} veces

Probabilidad base glosa: {(alto_riesgo/total)*100:.1f}%
Datos suficientes: {'SI' if datos['resumen']['archivos_procesados'] >= 10 else 'NO'}"""
        
        plt.text(0.1, 0.5, resumen_texto, fontsize=10, verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('metricas_dataset.png', dpi=300, bbox_inches='tight')
        print(f"\nGrafico guardado como: metricas_dataset.png")
        
    except Exception as e:
        print(f"Error creando grafico: {e}")
    
    print("\n" + "="*60)
    
    return {
        'total_validaciones': total,
        'alto_riesgo': alto_riesgo,
        'medio_riesgo': medio_riesgo,
        'bajo_riesgo': bajo_riesgo,
        'probabilidad_base': (alto_riesgo/total)*100
    }

if __name__ == "__main__":
    try:
        metricas = generar_reporte_simple()
        print("\nReporte de metricas generado exitosamente!")
        
    except Exception as e:
        print(f"Error generando reporte: {e}")
