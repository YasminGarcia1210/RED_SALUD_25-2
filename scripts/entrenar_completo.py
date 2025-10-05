#!/usr/bin/env python3
"""
Script completo para entrenar el modelo de glosa con datos reales
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.analizar_dataset import analizar_dataset
from scripts.entrenar_modelo_glosa import (
    ModeloGlosaMejorado, 
    crear_datos_entrenamiento
)
import json
from pathlib import Path

def main():
    """Función principal para entrenar el modelo completo"""
    
    print("🚀 INICIANDO ENTRENAMIENTO COMPLETO DEL MODELO DE GLOSA")
    print("=" * 60)
    
    # Paso 1: Analizar dataset existente
    print("\n📊 PASO 1: Analizando dataset existente...")
    try:
        analisis = analizar_dataset()
        print("✅ Análisis del dataset completado")
    except Exception as e:
        print(f"❌ Error analizando dataset: {e}")
        return False
    
    # Paso 2: Crear datos de entrenamiento
    print("\n📚 PASO 2: Creando datos de entrenamiento...")
    try:
        datos_entrenamiento = crear_datos_entrenamiento()
        if not datos_entrenamiento:
            print("❌ No se encontraron datos para entrenar")
            return False
        print(f"✅ Datos de entrenamiento creados: {len(datos_entrenamiento)} registros")
    except Exception as e:
        print(f"❌ Error creando datos de entrenamiento: {e}")
        return False
    
    # Paso 3: Entrenar modelo
    print("\n🧠 PASO 3: Entrenando modelo...")
    try:
        modelo = ModeloGlosaMejorado()
        modelo.entrenar(datos_entrenamiento)
        print("✅ Modelo entrenado exitosamente")
    except Exception as e:
        print(f"❌ Error entrenando modelo: {e}")
        return False
    
    # Paso 4: Guardar modelo
    print("\n💾 PASO 4: Guardando modelo...")
    try:
        modelo.guardar_modelo("modelo_glosa_entrenado.pkl")
        print("✅ Modelo guardado exitosamente")
    except Exception as e:
        print(f"❌ Error guardando modelo: {e}")
        return False
    
    # Paso 5: Probar modelo
    print("\n🧪 PASO 5: Probando modelo...")
    try:
        # Crear modelo de prueba
        modelo_prueba = ModeloGlosaMejorado("modelo_glosa_entrenado.pkl")
        
        # Probar con datos de ejemplo
        texto_factura_ejemplo = "Factura FERO941728 - Servicios médicos - CUPS 12345 - CIE Z749"
        texto_historia_ejemplo = "Historia clínica - Diagnóstico: Consulta general - Procedimiento: Examen físico"
        
        resultado = modelo_prueba.analizar_documentos(
            texto_factura_ejemplo, 
            texto_historia_ejemplo
        )
        
        print(f"✅ Prueba exitosa - Probabilidad: {resultado['probabilidad_glosa']}%")
        print(f"   Nivel de riesgo: {resultado['nivel_riesgo']}")
        
    except Exception as e:
        print(f"❌ Error probando modelo: {e}")
        return False
    
    print("\n🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE!")
    print("=" * 60)
    print("📁 Archivos generados:")
    print("   - analisis_dataset.json")
    print("   - modelo_glosa_entrenado.pkl")
    print("\n🚀 El modelo está listo para usar en FastAPI")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ Proceso falló")
        sys.exit(1)
