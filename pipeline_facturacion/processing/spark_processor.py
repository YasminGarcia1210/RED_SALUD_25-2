"""
Procesador distribuido con PySpark para el pipeline de facturación RIPS
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, udf, lit, when, array, struct
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType, ArrayType
from typing import List, Dict, Any, Optional
import json
import re
from pathlib import Path
from datetime import datetime

from ..config.settings import PipelineConfig
from ..utils.logger import setup_logger

class SparkRIPSProcessor:
    """Procesador distribuido con PySpark para archivos RIPS"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = setup_logger("spark_processor", {
            "log_level": config.log_level,
            "log_format": config.log_format
        })
        self.spark = self._create_spark_session()
        
        # Registrar UDFs
        self._register_udfs()
    
    def _create_spark_session(self) -> SparkSession:
        """Crea la sesión de Spark con configuración optimizada"""
        self.logger.info("Creando sesión de Spark", config=self.config.spark.dict())
        
        spark = SparkSession.builder \
            .appName(self.config.spark.app_name) \
            .master(self.config.spark.master) \
            .config("spark.driver.memory", self.config.spark.driver_memory) \
            .config("spark.executor.memory", self.config.spark.executor_memory) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.sql.adaptive.localShuffleReader.enabled", "true") \
            .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128m") \
            .config("spark.sql.adaptive.minNumPostShufflePartitions", "1") \
            .config("spark.sql.adaptive.maxNumPostShufflePartitions", "200") \
            .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256m") \
            .config("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5") \
            .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128m") \
            .config("spark.sql.adaptive.minNumPostShufflePartitions", "1") \
            .config("spark.sql.adaptive.maxNumPostShufflePartitions", "200") \
            .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256m") \
            .config("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5") \
            .getOrCreate()
        
        self.logger.info("Sesión de Spark creada exitosamente")
        return spark
    
    def _register_udfs(self):
        """Registra las funciones UDF personalizadas"""
        
        @udf(returnType=StringType())
        def extract_factura_number(file_path):
            """Extrae el número de factura del nombre del archivo"""
            if not file_path:
                return None
            
            match = re.search(r"FERO\d{6}", str(file_path))
            return match.group(0) if match else None
        
        @udf(returnType=StringType())
        def extract_document_type(text):
            """Extrae el tipo de documento del texto"""
            if not text:
                return None
            
            match = re.search(r"\b(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})", str(text))
            return match.group(1) if match else None
        
        @udf(returnType=StringType())
        def extract_document_number(text):
            """Extrae el número de documento del texto"""
            if not text:
                return None
            
            match = re.search(r"\b(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})", str(text))
            return match.group(2) if match else None
        
        @udf(returnType=StringType())
        def extract_birth_date(text):
            """Extrae la fecha de nacimiento del texto"""
            if not text:
                return None
            
            match = re.search(r"Fecha de Nacimiento y Edad:\s*(\d{2}/\d{2}/\d{4})", str(text))
            if match:
                try:
                    date_obj = datetime.strptime(match.group(1), "%d/%m/%Y")
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    return None
            return None
        
        @udf(returnType=StringType())
        def extract_sex_code(text):
            """Extrae el código de sexo del texto"""
            if not text:
                return None
            
            match = re.search(r"G[eé]nero:\s*(Femenino|Masculino)", str(text), re.IGNORECASE)
            if match:
                return "F" if "femenino" in match.group(1).lower() else "M"
            return None
        
        @udf(returnType=StringType())
        def extract_diagnosis(text):
            """Extrae el diagnóstico principal del texto"""
            if not text:
                return None
            
            match = re.search(r"DXP:\s*([A-Z]\d{2,4})", str(text))
            return match.group(1).strip() if match else None
        
        @udf(returnType=StringType())
        def extract_attention_date(text):
            """Extrae la fecha de atención del texto"""
            if not text:
                return None
            
            match = re.search(r"Fecha y Hora de Ingreso:\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})", str(text))
            if match:
                try:
                    date_obj = datetime.strptime(match.group(1), "%d/%m/%Y")
                    return f"{date_obj.strftime('%Y-%m-%d')} {match.group(2)}"
                except:
                    return None
            return None
        
        @udf(returnType=ArrayType(StringType()))
        def extract_cups_codes(text):
            """Extrae códigos CUPS del texto"""
            if not text:
                return []
            
            pattern = re.compile(r"(\d{6,8})\s+-\s+([A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s\-]+)")
            matches = pattern.findall(str(text))
            return [match[0] for match in matches]
        
        @udf(returnType=BooleanType())
        def was_service_given(text):
            """Determina si el servicio fue prestado"""
            if not text:
                return False
            
            text_lower = str(text).lower()
            
            frases_validas = [
                "se realiza", "se aplica", "se entrega", "se vacuna",
                "se atiende", "se atendió", "se valoró", "valorado", "atendido",
                "control realizado", "se hace control", "consulta realizada", 
                "paciente asistió", "realiza control", "realiza cita", "evaluado",
                "intervención realizada", "procedimiento realizado", "vacuna aplicada",
                "se ejecuta", "cita completada", "se cumplió", "realiza procedimiento",
                "se realiza la consulta", "se efectúa", "cita atendida", "asistió",
                "presente", "se presentó", "consulta realizada", "realizó la consulta",
                "cumple con la cita", "cumple cita", "cumple control"
            ]
            
            frases_no_atendido = [
                "no se presenta", "no asistió", "se cancela", "ausente",
                "cita no realizada", "no se realiza", "no se aplica", "paciente no viene",
                "cita cancelada", "no acude", "no acudió", "se inasiste", "inasistencia",
                "no se presentó", "cita incumplida", "no llega", "no asistió a cita",
                "paciente no asistió", "no se atiende", "no fue posible", 
                "se rechaza", "rechazada", "cita fallida", "no se ejecuta", "sin atención",
                "cita perdida", "no se completó", "no disponible", "no atendido",
                "cancelación", "cancelada por paciente", "no vino", "no pasó consulta"
            ]
            
            for frase in frases_no_atendido:
                if frase in text_lower:
                    return False
            
            for frase in frases_validas:
                if frase in text_lower:
                    return True
            
            return False
        
        # Registrar UDFs
        self.spark.udf.register("extract_factura_number", extract_factura_number)
        self.spark.udf.register("extract_document_type", extract_document_type)
        self.spark.udf.register("extract_document_number", extract_document_number)
        self.spark.udf.register("extract_birth_date", extract_birth_date)
        self.spark.udf.register("extract_sex_code", extract_sex_code)
        self.spark.udf.register("extract_diagnosis", extract_diagnosis)
        self.spark.udf.register("extract_attention_date", extract_attention_date)
        self.spark.udf.register("extract_cups_codes", extract_cups_codes)
        self.spark.udf.register("was_service_given", was_service_given)
        
        self.logger.info("UDFs registradas exitosamente")
    
    def process_hev_files(self, file_paths: List[str]) -> DataFrame:
        """
        Procesa archivos HEV en paralelo usando PySpark
        
        Args:
            file_paths: Lista de rutas de archivos HEV
            
        Returns:
            DataFrame: DataFrame con datos extraídos de HEV
        """
        self.logger.info(f"Iniciando procesamiento de archivos HEV", file_count=len(file_paths))
        
        # Schema para datos HEV
        hev_schema = StructType([
            StructField("file_path", StringType(), False),
            StructField("num_factura", StringType(), True),
            StructField("tipo_documento", StringType(), True),
            StructField("num_documento", StringType(), True),
            StructField("fecha_nacimiento", StringType(), True),
            StructField("cod_sexo", StringType(), True),
            StructField("cod_diagnostico", StringType(), True),
            StructField("fecha_atencion", StringType(), True),
            StructField("cups_codes", ArrayType(StringType()), True),
            StructField("servicio_prestado", BooleanType(), True),
            StructField("texto_completo", StringType(), True),
            StructField("procesamiento_exitoso", BooleanType(), True),
            StructField("error_mensaje", StringType(), True)
        ])
        
        # Crear DataFrame con rutas de archivos
        file_paths_df = self.spark.createDataFrame(file_paths, StringType()).toDF("file_path")
        
        # Procesar archivos en paralelo
        hev_df = file_paths_df.select(
            col("file_path"),
            extract_factura_number(col("file_path")).alias("num_factura"),
            extract_document_type(col("texto_completo")).alias("tipo_documento"),
            extract_document_number(col("texto_completo")).alias("num_documento"),
            extract_birth_date(col("texto_completo")).alias("fecha_nacimiento"),
            extract_sex_code(col("texto_completo")).alias("cod_sexo"),
            extract_diagnosis(col("texto_completo")).alias("cod_diagnostico"),
            extract_attention_date(col("texto_completo")).alias("fecha_atencion"),
            extract_cups_codes(col("texto_completo")).alias("cups_codes"),
            was_service_given(col("texto_completo")).alias("servicio_prestado"),
            col("texto_completo"),
            col("procesamiento_exitoso"),
            col("error_mensaje")
        )
        
        # Filtrar archivos procesados exitosamente
        hev_df = hev_df.filter(col("procesamiento_exitoso") == True)
        
        self.logger.info(
            f"Procesamiento de HEV completado",
            processed_files=hev_df.count(),
            total_files=len(file_paths)
        )
        
        return hev_df
    
    def process_xml_files(self, file_paths: List[str]) -> DataFrame:
        """
        Procesa archivos XML en paralelo usando PySpark
        
        Args:
            file_paths: Lista de rutas de archivos XML
            
        Returns:
            DataFrame: DataFrame con datos extraídos de XML
        """
        self.logger.info(f"Iniciando procesamiento de archivos XML", file_count=len(file_paths))
        
        # Schema para datos XML
        xml_schema = StructType([
            StructField("file_path", StringType(), False),
            StructField("num_factura", StringType(), True),
            StructField("fecha_emision", StringType(), True),
            StructField("nit_obligado", StringType(), True),
            StructField("valor_total", DoubleType(), True),
            StructField("cups_codes", ArrayType(StringType()), True),
            StructField("descripciones", ArrayType(StringType()), True),
            StructField("valores_unitarios", ArrayType(DoubleType()), True),
            StructField("procesamiento_exitoso", BooleanType(), True),
            StructField("error_mensaje", StringType(), True)
        ])
        
        # Crear DataFrame con rutas de archivos
        file_paths_df = self.spark.createDataFrame(file_paths, StringType()).toDF("file_path")
        
        # Procesar archivos en paralelo (simplificado para este ejemplo)
        xml_df = file_paths_df.select(
            col("file_path"),
            extract_factura_number(col("file_path")).alias("num_factura"),
            lit(None).cast(StringType()).alias("fecha_emision"),
            lit("805027337").alias("nit_obligado"),
            lit(9000.0).cast(DoubleType()).alias("valor_total"),
            array().cast(ArrayType(StringType())).alias("cups_codes"),
            array().cast(ArrayType(StringType())).alias("descripciones"),
            array().cast(ArrayType(DoubleType())).alias("valores_unitarios"),
            lit(True).alias("procesamiento_exitoso"),
            lit(None).cast(StringType()).alias("error_mensaje")
        )
        
        # Filtrar archivos procesados exitosamente
        xml_df = xml_df.filter(col("procesamiento_exitoso") == True)
        
        self.logger.info(
            f"Procesamiento de XML completado",
            processed_files=xml_df.count(),
            total_files=len(file_paths)
        )
        
        return xml_df
    
    def join_and_consolidate(self, hev_df: DataFrame, xml_df: DataFrame) -> DataFrame:
        """
        Consolida datos de HEV y XML
        
        Args:
            hev_df: DataFrame con datos de HEV
            xml_df: DataFrame con datos de XML
            
        Returns:
            DataFrame: DataFrame consolidado
        """
        self.logger.info("Iniciando consolidación de datos")
        
        # Join por número de factura
        consolidated_df = hev_df.join(
            xml_df,
            hev_df.num_factura == xml_df.num_factura,
            "inner"
        ).select(
            hev_df.num_factura,
            hev_df.tipo_documento,
            hev_df.num_documento,
            hev_df.fecha_nacimiento,
            hev_df.cod_sexo,
            hev_df.cod_diagnostico,
            hev_df.fecha_atencion,
            hev_df.cups_codes,
            hev_df.servicio_prestado,
            xml_df.nit_obligado,
            xml_df.valor_total,
            xml_df.descripciones,
            xml_df.valores_unitarios
        )
        
        # Filtrar solo servicios prestados
        consolidated_df = consolidated_df.filter(col("servicio_prestado") == True)
        
        self.logger.info(
            f"Consolidación completada",
            total_records=consolidated_df.count()
        )
        
        return consolidated_df
    
    def generate_rips_dataframe(self, consolidated_df: DataFrame) -> DataFrame:
        """
        Genera DataFrame con estructura RIPS
        
        Args:
            consolidated_df: DataFrame consolidado
            
        Returns:
            DataFrame: DataFrame con estructura RIPS
        """
        self.logger.info("Generando estructura RIPS")
        
        # Crear estructura RIPS
        rips_df = consolidated_df.select(
            col("num_factura").alias("numFactura"),
            col("nit_obligado").alias("numDocumentoIdObligado"),
            struct(
                col("tipo_documento").alias("tipoDocumentoIdentificacion"),
                col("num_documento").alias("numDocumentoIdentificacion"),
                col("fecha_nacimiento").alias("fechaNacimiento"),
                col("cod_sexo").alias("codSexo"),
                col("cod_diagnostico").alias("codDiagnosticoPrincipal"),
                col("fecha_atencion").alias("fechaInicioAtencion"),
                struct(
                    col("cups_codes").alias("procedimientos")
                ).alias("servicios")
            ).alias("usuarios")
        )
        
        self.logger.info(f"Estructura RIPS generada", records=rips_df.count())
        
        return rips_df
    
    def save_rips_files(self, rips_df: DataFrame, output_path: Path):
        """
        Guarda archivos RIPS individuales
        
        Args:
            rips_df: DataFrame con estructura RIPS
            output_path: Ruta de salida
        """
        self.logger.info(f"Guardando archivos RIPS", output_path=str(output_path))
        
        # Crear directorio de salida
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Convertir a Pandas para procesamiento individual
        pandas_df = rips_df.toPandas()
        
        for _, row in pandas_df.iterrows():
            num_factura = row["numFactura"]
            if num_factura:
                rips_data = {
                    "numNota": None,
                    "tipoNota": None,
                    "usuarios": [row["usuarios"]],
                    "numFactura": num_factura,
                    "numDocumentoIdObligado": row["numDocumentoIdObligado"]
                }
                
                # Guardar archivo JSON
                output_file = output_path / f"{num_factura}_Rips.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(rips_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Archivos RIPS guardados", file_count=len(pandas_df))
    
    def process_pipeline(self, hev_files: List[str], xml_files: List[str], output_path: Path):
        """
        Ejecuta el pipeline completo de procesamiento
        
        Args:
            hev_files: Lista de archivos HEV
            xml_files: Lista de archivos XML
            output_path: Ruta de salida
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando pipeline de procesamiento",
            hev_files=len(hev_files),
            xml_files=len(xml_files)
        )
        
        try:
            # Procesar archivos HEV
            hev_df = self.process_hev_files(hev_files)
            
            # Procesar archivos XML
            xml_df = self.process_xml_files(xml_files)
            
            # Consolidar datos
            consolidated_df = self.join_and_consolidate(hev_df, xml_df)
            
            # Generar estructura RIPS
            rips_df = self.generate_rips_dataframe(consolidated_df)
            
            # Guardar archivos
            self.save_rips_files(rips_df, output_path)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"Pipeline completado exitosamente",
                processing_time_seconds=processing_time,
                output_path=str(output_path)
            )
            
        except Exception as e:
            self.logger.error(f"Error en pipeline de procesamiento", error=str(e))
            raise
    
    def stop(self):
        """Detiene la sesión de Spark"""
        if self.spark:
            self.spark.stop()
            self.logger.info("Sesión de Spark detenida")

