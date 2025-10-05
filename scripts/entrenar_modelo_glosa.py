#!/usr/bin/env python3
"""
Script para entrenar un modelo mejorado de predicción de glosa
basado en datos reales de validaciones.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import re

class ModeloGlosaMejorado:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='spanish')
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.codigos_riesgo = self._cargar_codigos_riesgo()
        
    def _cargar_codigos_riesgo(self):
        """Carga códigos de validación y sus niveles de riesgo"""
        return {
            # Códigos de ALTO riesgo (probable glosa)
            'RVC033': 0.9,  # CIE no válido
            'RVG19': 0.8,   # Validación PSS/PTS no permitida
            'RVC019': 0.7,  # CUPS no válido
            'RVC001': 0.8,   # Error en datos básicos
            'RVC002': 0.7,   # Error en fechas
            
            # Códigos de MEDIO riesgo
            'RVC010': 0.5,   # Advertencia menor
            'RVC015': 0.4,   # Notificación
            
            # Códigos de BAJO riesgo
            'RVC005': 0.2,   # Información
            'RVC008': 0.1,   # Sugerencia
        }
    
    def extraer_caracteristicas(self, texto_factura, texto_historia, validaciones_json=None):
        """Extrae características de los documentos"""
        caracteristicas = {}
        
        # 1. Análisis de texto con TF-IDF
        texto_combinado = f"{texto_factura} {texto_historia}"
        
        # 2. Características específicas de factura
        caracteristicas.update(self._analizar_factura(texto_factura))
        
        # 3. Características específicas de historia clínica
        caracteristicas.update(self._analizar_historia(texto_historia))
        
        # 4. Coherencia entre documentos
        caracteristicas.update(self._analizar_coherencia(texto_factura, texto_historia))
        
        # 5. Si hay validaciones JSON, usarlas
        if validaciones_json:
            caracteristicas.update(self._analizar_validaciones(validaciones_json))
        
        return caracteristicas
    
    def _analizar_factura(self, texto):
        """Analiza características específicas de la factura"""
        caracteristicas = {}
        
        # Buscar códigos CUPS
        cups_pattern = r'CUPS[:\s]*(\d+)'
        cups_matches = re.findall(cups_pattern, texto, re.IGNORECASE)
        caracteristicas['num_cups'] = len(cups_matches)
        
        # Buscar códigos CIE
        cie_pattern = r'CIE[:\s]*([A-Z]\d+)'
        cie_matches = re.findall(cie_pattern, texto, re.IGNORECASE)
        caracteristicas['num_cie'] = len(cie_matches)
        
        # Buscar montos
        monto_pattern = r'\$[\d,]+\.?\d*'
        montos = re.findall(monto_pattern, texto)
        caracteristicas['num_montos'] = len(montos)
        
        # Buscar fechas
        fecha_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        fechas = re.findall(fecha_pattern, texto)
        caracteristicas['num_fechas'] = len(fechas)
        
        # Longitud del texto
        caracteristicas['longitud_factura'] = len(texto)
        
        return caracteristicas
    
    def _analizar_historia(self, texto):
        """Analiza características específicas de la historia clínica"""
        caracteristicas = {}
        
        # Palabras clave médicas
        palabras_medicas = ['diagnóstico', 'tratamiento', 'síntomas', 'examen', 'procedimiento']
        caracteristicas['palabras_medicas'] = sum(1 for palabra in palabras_medicas 
                                                if palabra.lower() in texto.lower())
        
        # Buscar diagnósticos
        diag_pattern = r'diagnóstico[:\s]*([^.\n]+)'
        diagnosticos = re.findall(diag_pattern, texto, re.IGNORECASE)
        caracteristicas['num_diagnosticos'] = len(diagnosticos)
        
        # Longitud del texto
        caracteristicas['longitud_historia'] = len(texto)
        
        return caracteristicas
    
    def _analizar_coherencia(self, texto_factura, texto_historia):
        """Analiza coherencia entre factura e historia clínica"""
        caracteristicas = {}
        
        # Buscar códigos comunes
        cups_factura = set(re.findall(r'CUPS[:\s]*(\d+)', texto_factura, re.IGNORECASE))
        cups_historia = set(re.findall(r'CUPS[:\s]*(\d+)', texto_historia, re.IGNORECASE))
        
        caracteristicas['cups_coincidentes'] = len(cups_factura.intersection(cups_historia))
        caracteristicas['cups_solo_factura'] = len(cups_factura - cups_historia)
        caracteristicas['cups_solo_historia'] = len(cups_historia - cups_factura)
        
        # Coherencia de fechas
        fechas_factura = set(re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', texto_factura))
        fechas_historia = set(re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', texto_historia))
        
        caracteristicas['fechas_coincidentes'] = len(fechas_factura.intersection(fechas_historia))
        
        return caracteristicas
    
    def _analizar_validaciones(self, validaciones_json):
        """Analiza las validaciones JSON para extraer características"""
        caracteristicas = {}
        
        if 'ResultadosValidacion' in validaciones_json:
            validaciones = validaciones_json['ResultadosValidacion']
            
            # Contar por clase
            clases = [v.get('Clase', '') for v in validaciones]
            caracteristicas['num_notificaciones'] = clases.count('NOTIFICACION')
            caracteristicas['num_errores'] = clases.count('ERROR')
            caracteristicas['num_advertencias'] = clases.count('ADVERTENCIA')
            
            # Calcular riesgo basado en códigos
            riesgo_total = 0
            for validacion in validaciones:
                codigo = validacion.get('Codigo', '')
                if codigo in self.codigos_riesgo:
                    riesgo_total += self.codigos_riesgo[codigo]
            
            caracteristicas['riesgo_validaciones'] = riesgo_total / len(validaciones) if validaciones else 0
            
            # Contar códigos específicos
            codigos = [v.get('Codigo', '') for v in validaciones]
            for codigo in self.codigos_riesgo:
                caracteristicas[f'codigo_{codigo}'] = codigos.count(codigo)
        
        return caracteristicas
    
    def entrenar(self, datos_entrenamiento):
        """Entrena el modelo con datos de entrenamiento"""
        print("🧠 Entrenando modelo mejorado...")
        
        # Preparar datos
        X = []
        y = []
        
        for dato in datos_entrenamiento:
            caracteristicas = self.extraer_caracteristicas(
                dato['texto_factura'],
                dato['texto_historia'],
                dato.get('validaciones_json')
            )
            
            X.append(list(caracteristicas.values()))
            y.append(dato['probabilidad_glosa_real'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Entrenar modelo
        self.model.fit(X, y)
        
        # Evaluar
        y_pred = self.model.predict(X)
        print("📊 Métricas de entrenamiento:")
        print(classification_report(y, y_pred))
        
        return self.model
    
    def predecir(self, texto_factura, texto_historia, validaciones_json=None):
        """Predice la probabilidad de glosa"""
        caracteristicas = self.extraer_caracteristicas(
            texto_factura, texto_historia, validaciones_json
        )
        
        X = np.array([list(caracteristicas.values())])
        probabilidad = self.model.predict_proba(X)[0][1]  # Probabilidad de clase positiva
        
        return {
            'probabilidad_glosa': int(probabilidad * 100),
            'nivel_riesgo': self._determinar_nivel_riesgo(probabilidad),
            'caracteristicas_analizadas': caracteristicas
        }
    
    def _determinar_nivel_riesgo(self, probabilidad):
        """Determina el nivel de riesgo basado en la probabilidad"""
        if probabilidad >= 0.7:
            return "ALTO"
        elif probabilidad >= 0.4:
            return "MEDIO"
        else:
            return "BAJO"
    
    def guardar_modelo(self, ruta="modelo_glosa_mejorado.pkl"):
        """Guarda el modelo entrenado"""
        joblib.dump({
            'model': self.model,
            'vectorizer': self.vectorizer,
            'codigos_riesgo': self.codigos_riesgo
        }, ruta)
        print(f"💾 Modelo guardado en: {ruta}")

def crear_datos_entrenamiento():
    """Crea datos de entrenamiento basados en el dataset existente"""
    print("📚 Creando datos de entrenamiento...")
    
    base_path = Path("FEV_JSON-20250807T191037Z-1-001/FEV_JSON")
    datos_entrenamiento = []
    
    for carpeta in base_path.iterdir():
        if carpeta.is_dir():
            # Buscar archivos
            json_files = list(carpeta.glob("*.json"))
            pdf_factura = list(carpeta.glob("*FDE*.pdf"))
            pdf_historia = list(carpeta.glob("*HEV*.pdf"))
            
            if json_files and pdf_factura and pdf_historia:
                try:
                    # Cargar JSON de validaciones
                    with open(json_files[0], 'r', encoding='utf-8') as f:
                        validaciones = json.load(f)
                    
                    # Calcular probabilidad real basada en validaciones
                    probabilidad_real = calcular_probabilidad_real(validaciones)
                    
                    # Simular texto de PDFs (en producción se extraería con OCR)
                    texto_factura = f"Factura {carpeta.name} - Contenido simulado"
                    texto_historia = f"Historia clínica {carpeta.name} - Contenido simulado"
                    
                    datos_entrenamiento.append({
                        'texto_factura': texto_factura,
                        'texto_historia': texto_historia,
                        'validaciones_json': validaciones,
                        'probabilidad_glosa_real': probabilidad_real
                    })
                    
                except Exception as e:
                    print(f"❌ Error procesando {carpeta.name}: {e}")
    
    print(f"✅ Datos de entrenamiento creados: {len(datos_entrenamiento)} registros")
    return datos_entrenamiento

def calcular_probabilidad_real(validaciones_json):
    """Calcula la probabilidad real de glosa basada en las validaciones"""
    if 'ResultadosValidacion' not in validaciones_json:
        return 0.5  # Neutral si no hay validaciones
    
    validaciones = validaciones_json['ResultadosValidacion']
    if not validaciones:
        return 0.5
    
    # Mapeo de códigos a probabilidades
    codigos_riesgo = {
        'RVC033': 0.9,  # CIE no válido
        'RVG19': 0.8,   # Validación PSS/PTS
        'RVC019': 0.7,  # CUPS no válido
        'RVC001': 0.8,   # Error datos básicos
        'RVC002': 0.7,   # Error fechas
        'RVC010': 0.5,   # Advertencia
        'RVC015': 0.4,   # Notificación
        'RVC005': 0.2,   # Información
        'RVC008': 0.1,   # Sugerencia
    }
    
    # Calcular probabilidad promedio
    probabilidades = []
    for validacion in validaciones:
        codigo = validacion.get('Codigo', '')
        if codigo in codigos_riesgo:
            probabilidades.append(codigos_riesgo[codigo])
        else:
            probabilidades.append(0.3)  # Valor por defecto
    
    return np.mean(probabilidades) if probabilidades else 0.5

if __name__ == "__main__":
    # Crear y entrenar modelo
    modelo = ModeloGlosaMejorado()
    datos_entrenamiento = crear_datos_entrenamiento()
    
    if datos_entrenamiento:
        modelo.entrenar(datos_entrenamiento)
        modelo.guardar_modelo()
        print("🎉 Modelo entrenado y guardado exitosamente!")
    else:
        print("❌ No se encontraron datos para entrenar")
