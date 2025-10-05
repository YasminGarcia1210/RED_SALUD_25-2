"""
Módulo para el modelo mejorado de predicción de glosa
"""

import joblib
import numpy as np
import re
from typing import Dict, Any, Optional
import json

class ModeloGlosaMejorado:
    def __init__(self, ruta_modelo: str = "modelo_glosa_mejorado.pkl"):
        self.ruta_modelo = ruta_modelo
        self.model = None
        self.vectorizer = None
        self.codigos_riesgo = self._cargar_codigos_riesgo()
        self._cargar_modelo()
    
    def _cargar_codigos_riesgo(self):
        """Códigos de validación y sus niveles de riesgo"""
        return {
            # ALTO riesgo (probable glosa)
            'RVC033': 0.9,  # CIE no válido
            'RVG19': 0.8,   # Validación PSS/PTS no permitida
            'RVC019': 0.7,  # CUPS no válido
            'RVC001': 0.8,   # Error en datos básicos
            'RVC002': 0.7,   # Error en fechas
            'RVC003': 0.8,   # Error en valores
            'RVC004': 0.7,   # Error en códigos
            
            # MEDIO riesgo
            'RVC010': 0.5,   # Advertencia menor
            'RVC015': 0.4,   # Notificación
            'RVC020': 0.5,   # Sugerencia importante
            
            # BAJO riesgo
            'RVC005': 0.2,   # Información
            'RVC008': 0.1,   # Sugerencia
            'RVC012': 0.1,   # Recomendación
        }
    
    def _cargar_modelo(self):
        """Carga el modelo entrenado"""
        try:
            modelo_data = joblib.load(self.ruta_modelo)
            self.model = modelo_data['model']
            self.vectorizer = modelo_data['vectorizer']
            print("✅ Modelo de glosa cargado exitosamente")
        except FileNotFoundError:
            print("⚠️ Modelo no encontrado, usando modelo por defecto")
            self.model = None
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            self.model = None
    
    def analizar_documentos(self, texto_factura: str, texto_historia: str, 
                          validaciones_json: Optional[Dict] = None) -> Dict[str, Any]:
        """Analiza documentos y predice probabilidad de glosa"""
        
        # Extraer características
        caracteristicas = self._extraer_caracteristicas(
            texto_factura, texto_historia, validaciones_json
        )
        
        # Calcular probabilidad
        if self.model:
            probabilidad = self._predecir_con_modelo(caracteristicas)
        else:
            probabilidad = self._predecir_heuristica(caracteristicas, validaciones_json)
        
        # Generar análisis detallado
        analisis = self._generar_analisis_detallado(
            caracteristicas, probabilidad, validaciones_json
        )
        
        return analisis
    
    def _extraer_caracteristicas(self, texto_factura: str, texto_historia: str, 
                               validaciones_json: Optional[Dict] = None) -> Dict[str, float]:
        """Extrae características de los documentos"""
        caracteristicas = {}
        
        # 1. Análisis de factura
        caracteristicas.update(self._analizar_factura(texto_factura))
        
        # 2. Análisis de historia clínica
        caracteristicas.update(self._analizar_historia(texto_historia))
        
        # 3. Coherencia entre documentos
        caracteristicas.update(self._analizar_coherencia(texto_factura, texto_historia))
        
        # 4. Análisis de validaciones (si están disponibles)
        if validaciones_json:
            caracteristicas.update(self._analizar_validaciones(validaciones_json))
        
        return caracteristicas
    
    def _analizar_factura(self, texto: str) -> Dict[str, float]:
        """Analiza características específicas de la factura"""
        caracteristicas = {}
        
        # Códigos CUPS
        cups_pattern = r'CUPS[:\s]*(\d+)'
        cups_matches = re.findall(cups_pattern, texto, re.IGNORECASE)
        caracteristicas['num_cups'] = len(cups_matches)
        
        # Códigos CIE
        cie_pattern = r'CIE[:\s]*([A-Z]\d+)'
        cie_matches = re.findall(cie_pattern, texto, re.IGNORECASE)
        caracteristicas['num_cie'] = len(cie_matches)
        
        # Montos monetarios
        monto_pattern = r'\$[\d,]+\.?\d*'
        montos = re.findall(monto_pattern, texto)
        caracteristicas['num_montos'] = len(montos)
        
        # Fechas
        fecha_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        fechas = re.findall(fecha_pattern, texto)
        caracteristicas['num_fechas'] = len(fechas)
        
        # Longitud del texto
        caracteristicas['longitud_factura'] = len(texto)
        
        # Densidad de información
        caracteristicas['densidad_info'] = len(re.findall(r'\w+', texto)) / max(len(texto), 1)
        
        return caracteristicas
    
    def _analizar_historia(self, texto: str) -> Dict[str, float]:
        """Analiza características específicas de la historia clínica"""
        caracteristicas = {}
        
        # Palabras clave médicas
        palabras_medicas = [
            'diagnóstico', 'tratamiento', 'síntomas', 'examen', 'procedimiento',
            'medicamento', 'dosis', 'frecuencia', 'duración', 'evolución'
        ]
        caracteristicas['palabras_medicas'] = sum(
            1 for palabra in palabras_medicas 
            if palabra.lower() in texto.lower()
        )
        
        # Diagnósticos
        diag_pattern = r'diagnóstico[:\s]*([^.\n]+)'
        diagnosticos = re.findall(diag_pattern, texto, re.IGNORECASE)
        caracteristicas['num_diagnosticos'] = len(diagnosticos)
        
        # Procedimientos
        proc_pattern = r'procedimiento[:\s]*([^.\n]+)'
        procedimientos = re.findall(proc_pattern, texto, re.IGNORECASE)
        caracteristicas['num_procedimientos'] = len(procedimientos)
        
        # Longitud del texto
        caracteristicas['longitud_historia'] = len(texto)
        
        return caracteristicas
    
    def _analizar_coherencia(self, texto_factura: str, texto_historia: str) -> Dict[str, float]:
        """Analiza coherencia entre factura e historia clínica"""
        caracteristicas = {}
        
        # Códigos CUPS
        cups_factura = set(re.findall(r'CUPS[:\s]*(\d+)', texto_factura, re.IGNORECASE))
        cups_historia = set(re.findall(r'CUPS[:\s]*(\d+)', texto_historia, re.IGNORECASE))
        
        caracteristicas['cups_coincidentes'] = len(cups_factura.intersection(cups_historia))
        caracteristicas['cups_solo_factura'] = len(cups_factura - cups_historia)
        caracteristicas['cups_solo_historia'] = len(cups_historia - cups_factura)
        
        # Coherencia de fechas
        fechas_factura = set(re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', texto_factura))
        fechas_historia = set(re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', texto_historia))
        
        caracteristicas['fechas_coincidentes'] = len(fechas_factura.intersection(fechas_historia))
        caracteristicas['fechas_solo_factura'] = len(fechas_factura - fechas_historia)
        caracteristicas['fechas_solo_historia'] = len(fechas_historia - fechas_factura)
        
        # Coherencia general
        caracteristicas['coherencia_general'] = (
            caracteristicas['cups_coincidentes'] + 
            caracteristicas['fechas_coincidentes']
        ) / max(len(cups_factura) + len(fechas_factura), 1)
        
        return caracteristicas
    
    def _analizar_validaciones(self, validaciones_json: Dict) -> Dict[str, float]:
        """Analiza las validaciones JSON"""
        caracteristicas = {}
        
        if 'ResultadosValidacion' not in validaciones_json:
            return caracteristicas
        
        validaciones = validaciones_json['ResultadosValidacion']
        
        # Contar por clase
        clases = [v.get('Clase', '') for v in validaciones]
        caracteristicas['num_notificaciones'] = clases.count('NOTIFICACION')
        caracteristicas['num_errores'] = clases.count('ERROR')
        caracteristicas['num_advertencias'] = clases.count('ADVERTENCIA')
        
        # Calcular riesgo basado en códigos
        riesgo_total = 0
        codigos_encontrados = []
        
        for validacion in validaciones:
            codigo = validacion.get('Codigo', '')
            if codigo in self.codigos_riesgo:
                riesgo_total += self.codigos_riesgo[codigo]
                codigos_encontrados.append(codigo)
        
        caracteristicas['riesgo_validaciones'] = (
            riesgo_total / len(validaciones) if validaciones else 0
        )
        
        # Contar códigos específicos
        codigos = [v.get('Codigo', '') for v in validaciones]
        for codigo in self.codigos_riesgo:
            caracteristicas[f'codigo_{codigo}'] = codigos.count(codigo)
        
        caracteristicas['codigos_riesgo_encontrados'] = len(codigos_encontrados)
        
        return caracteristicas
    
    def _predecir_con_modelo(self, caracteristicas: Dict[str, float]) -> float:
        """Predice usando el modelo entrenado"""
        try:
            X = np.array([list(caracteristicas.values())])
            probabilidad = self.model.predict_proba(X)[0][1]
            return probabilidad
        except Exception as e:
            print(f"❌ Error en predicción del modelo: {e}")
            return 0.5
    
    def _predecir_heuristica(self, caracteristicas: Dict[str, float], 
                           validaciones_json: Optional[Dict] = None) -> float:
        """Predice usando heurísticas cuando no hay modelo entrenado"""
        
        # Factores de riesgo
        factores_riesgo = []
        
        # 1. Coherencia entre documentos
        coherencia = caracteristicas.get('coherencia_general', 0)
        if coherencia < 0.3:
            factores_riesgo.append(0.8)
        
        # 2. Códigos no coincidentes
        cups_solo_factura = caracteristicas.get('cups_solo_factura', 0)
        if cups_solo_factura > 2:
            factores_riesgo.append(0.6)
        
        # 3. Validaciones JSON
        if validaciones_json and 'ResultadosValidacion' in validaciones_json:
            validaciones = validaciones_json['ResultadosValidacion']
            for validacion in validaciones:
                codigo = validacion.get('Codigo', '')
                if codigo in self.codigos_riesgo:
                    factores_riesgo.append(self.codigos_riesgo[codigo])
        
        # 4. Densidad de información
        densidad = caracteristicas.get('densidad_info', 0)
        if densidad < 0.1:  # Muy poca información
            factores_riesgo.append(0.7)
        
        # Calcular probabilidad promedio
        if factores_riesgo:
            return np.mean(factores_riesgo)
        else:
            return 0.5  # Neutral
    
    def _generar_analisis_detallado(self, caracteristicas: Dict[str, float], 
                                  probabilidad: float, 
                                  validaciones_json: Optional[Dict] = None) -> Dict[str, Any]:
        """Genera análisis detallado del resultado"""
        
        nivel_riesgo = self._determinar_nivel_riesgo(probabilidad)
        
        # Factores de riesgo identificados
        factores_riesgo = []
        if caracteristicas.get('coherencia_general', 0) < 0.3:
            factores_riesgo.append("Baja coherencia entre factura e historia clínica")
        
        if caracteristicas.get('cups_solo_factura', 0) > 2:
            factores_riesgo.append("Códigos CUPS en factura no justificados en historia")
        
        if caracteristicas.get('densidad_info', 0) < 0.1:
            factores_riesgo.append("Información insuficiente en los documentos")
        
        # Recomendaciones
        recomendaciones = []
        if probabilidad > 0.7:
            recomendaciones.append("Revisar coherencia entre factura e historia clínica")
            recomendaciones.append("Verificar códigos CUPS y CIE")
            recomendaciones.append("Validar fechas de atención")
        
        if caracteristicas.get('num_diagnosticos', 0) == 0:
            recomendaciones.append("Incluir diagnósticos claros en la historia clínica")
        
        # Puntuación detallada
        puntuacion_detallada = {
            "coherencia_diagnostica": int(caracteristicas.get('coherencia_general', 0) * 100),
            "justificacion_medica": int(caracteristicas.get('palabras_medicas', 0) * 10),
            "cumplimiento_normativo": int((1 - probabilidad) * 100),
            "calidad_documental": int(caracteristicas.get('densidad_info', 0) * 100)
        }
        
        return {
            "probabilidad_glosa": int(probabilidad * 100),
            "nivel_riesgo": nivel_riesgo,
            "factores_riesgo": factores_riesgo,
            "recomendaciones": recomendaciones,
            "puntuacion_detallada": puntuacion_detallada,
            "caracteristicas_analizadas": caracteristicas
        }
    
    def _determinar_nivel_riesgo(self, probabilidad: float) -> str:
        """Determina el nivel de riesgo"""
        if probabilidad >= 0.7:
            return "ALTO"
        elif probabilidad >= 0.4:
            return "MEDIO"
        else:
            return "BAJO"
