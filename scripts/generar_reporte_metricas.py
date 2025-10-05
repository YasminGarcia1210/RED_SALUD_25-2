#!/usr/bin/env python3
"""
Script para generar un reporte visual de las métricas del dataset
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import pandas as pd

def generar_reporte_visual():
    """Genera reporte visual de las métricas"""
    
    # Cargar análisis
    with open("analisis_dataset.json", "r", encoding="utf-8") as f:
        datos = json.load(f)
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Crear figura con subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('📊 MÉTRICAS DEL DATASET DE VALIDACIONES', fontsize=16, fontweight='bold')
    
    # 1. Gráfico de códigos de validación más frecuentes
    ax1 = axes[0, 0]
    codigos = datos['codigos_validacion']
    codigos_ordenados = sorted(codigos.items(), key=lambda x: x[1], reverse=True)[:8]
    
    codigos_nombres = [codigo for codigo, _ in codigos_ordenados]
    codigos_valores = [valor for _, valor in codigos_ordenados]
    
    bars1 = ax1.bar(codigos_nombres, codigos_valores, color='skyblue', edgecolor='navy', alpha=0.7)
    ax1.set_title('🔝 Códigos de Validación Más Frecuentes', fontweight='bold')
    ax1.set_xlabel('Código de Validación')
    ax1.set_ylabel('Frecuencia')
    ax1.tick_params(axis='x', rotation=45)
    
    # Añadir valores en las barras
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Distribución de clases de validación
    ax2 = axes[0, 1]
    clases = datos['clases_validacion']
    clases_nombres = list(clases.keys())
    clases_valores = list(clases.values())
    
    colors = ['lightcoral', 'lightgreen', 'lightskyblue', 'lightpink']
    wedges, texts, autotexts = ax2.pie(clases_valores, labels=clases_nombres, autopct='%1.1f%%',
                                       colors=colors[:len(clases_nombres)], startangle=90)
    ax2.set_title('📋 Distribución de Clases de Validación', fontweight='bold')
    
    # 3. Análisis de riesgo por código
    ax3 = axes[1, 0]
    
    # Mapeo de códigos a nivel de riesgo
    codigos_riesgo = {
        'RVC033': 'ALTO',    # CIE no válido
        'RVG19': 'ALTO',     # Validación PSS/PTS
        'RVC019': 'MEDIO',   # CUPS validación
        'RVC051': 'MEDIO',   # Finalidad
        'RVC065': 'BAJO',    # Otros
        'RVC063': 'BAJO',
        'RVC059': 'BAJO',
        'RVC005': 'BAJO',
        'RVC017': 'BAJO',
        'RVC071': 'BAJO'
    }
    
    # Contar por nivel de riesgo
    riesgo_counts = {'ALTO': 0, 'MEDIO': 0, 'BAJO': 0}
    for codigo, count in codigos.items():
        nivel = codigos_riesgo.get(codigo, 'BAJO')
        riesgo_counts[nivel] += count
    
    niveles = list(riesgo_counts.keys())
    valores_riesgo = list(riesgo_counts.values())
    colores_riesgo = ['red', 'orange', 'green']
    
    bars3 = ax3.bar(niveles, valores_riesgo, color=colores_riesgo, alpha=0.7, edgecolor='black')
    ax3.set_title('⚠️ Distribución por Nivel de Riesgo', fontweight='bold')
    ax3.set_xlabel('Nivel de Riesgo')
    ax3.set_ylabel('Cantidad de Validaciones')
    
    # Añadir valores en las barras
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Resumen estadístico
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Calcular estadísticas
    total_validaciones = sum(codigos.values())
    codigo_mas_frecuente = max(codigos.items(), key=lambda x: x[1])
    porcentaje_notificaciones = (datos['clases_validacion']['NOTIFICACION'] / total_validaciones) * 100
    
    # Crear texto del resumen
    resumen_texto = f"""
    📊 RESUMEN ESTADÍSTICO
    
    📁 Archivos Procesados: {datos['resumen']['archivos_procesados']}
    🔍 Total Validaciones: {total_validaciones}
    ❌ Errores: {datos['resumen']['errores_encontrados']}
    
    🏆 Código Más Frecuente:
    {codigo_mas_frecuente[0]}: {codigo_mas_frecuente[1]} veces
    
    📋 Clases de Validación:
    NOTIFICACIÓN: {porcentaje_notificaciones:.1f}%
    
    ⚠️ Análisis de Riesgo:
    • ALTO: {riesgo_counts['ALTO']} validaciones
    • MEDIO: {riesgo_counts['MEDIO']} validaciones  
    • BAJO: {riesgo_counts['BAJO']} validaciones
    
    🎯 Recomendaciones:
    • Enfocar en códigos RVC033 y RVG19 (alto riesgo)
    • Mejorar validación de CUPS (RVC019)
    • Revisar códigos CIE inválidos
    """
    
    ax4.text(0.05, 0.95, resumen_texto, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    # Ajustar layout
    plt.tight_layout()
    
    # Guardar gráfico
    plt.savefig('metricas_dataset.png', dpi=300, bbox_inches='tight')
    print("📊 Gráfico guardado como: metricas_dataset.png")
    
    # Mostrar gráfico
    plt.show()
    
    return {
        'total_validaciones': total_validaciones,
        'codigo_mas_frecuente': codigo_mas_frecuente,
        'riesgo_counts': riesgo_counts,
        'porcentaje_notificaciones': porcentaje_notificaciones
    }

def generar_reporte_texto():
    """Genera reporte de texto con recomendaciones"""
    
    with open("analisis_dataset.json", "r", encoding="utf-8") as f:
        datos = json.load(f)
    
    print("\n" + "="*60)
    print("📊 REPORTE DETALLADO DE MÉTRICAS DEL DATASET")
    print("="*60)
    
    print(f"\n📁 DATOS GENERALES:")
    print(f"   • Archivos procesados: {datos['resumen']['archivos_procesados']}")
    print(f"   • Total validaciones: {sum(datos['codigos_validacion'].values())}")
    print(f"   • Errores encontrados: {datos['resumen']['errores_encontrados']}")
    
    print(f"\n🔝 TOP 5 CÓDIGOS MÁS PROBLEMÁTICOS:")
    codigos_ordenados = sorted(datos['codigos_validacion'].items(), key=lambda x: x[1], reverse=True)
    for i, (codigo, count) in enumerate(codigos_ordenados[:5], 1):
        print(f"   {i}. {codigo}: {count} ocurrencias")
    
    print(f"\n⚠️ ANÁLISIS DE RIESGO:")
    codigos_riesgo = {
        'RVC033': ('CIE no válido', 'ALTO'),
        'RVG19': ('Validación PSS/PTS', 'ALTO'),
        'RVC019': ('CUPS validación', 'MEDIO'),
        'RVC051': ('Finalidad', 'MEDIO'),
        'RVC065': ('Otros', 'BAJO')
    }
    
    for codigo, (descripcion, riesgo) in codigos_riesgo.items():
        if codigo in datos['codigos_validacion']:
            count = datos['codigos_validacion'][codigo]
            print(f"   • {codigo} ({descripcion}): {count} veces - RIESGO {riesgo}")
    
    print(f"\n🎯 RECOMENDACIONES PARA EL MODELO:")
    print(f"   1. Priorizar códigos RVC033 y RVG19 (alto riesgo de glosa)")
    print(f"   2. Mejorar detección de códigos CIE inválidos")
    print(f"   3. Validar coherencia entre CUPS y diagnósticos")
    print(f"   4. Revisar validaciones PSS/PTS")
    print(f"   5. Implementar pesos específicos por código de riesgo")
    
    print(f"\n📈 MÉTRICAS PARA ENTRENAMIENTO:")
    total = sum(datos['codigos_validacion'].values())
    alto_riesgo = datos['codigos_validacion'].get('RVC033', 0) + datos['codigos_validacion'].get('RVG19', 0)
    print(f"   • Probabilidad base de glosa: {(alto_riesgo/total)*100:.1f}%")
    print(f"   • Códigos de alto riesgo: {alto_riesgo}/{total} ({(alto_riesgo/total)*100:.1f}%)")
    print(f"   • Datos suficientes para entrenamiento: {'SÍ' if datos['resumen']['archivos_procesados'] >= 10 else 'NO'}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        # Generar reporte visual
        metricas = generar_reporte_visual()
        
        # Generar reporte de texto
        generar_reporte_texto()
        
        print("\n✅ Reporte de métricas generado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        print("💡 Asegúrate de tener matplotlib y seaborn instalados:")
        print("   pip install matplotlib seaborn")
