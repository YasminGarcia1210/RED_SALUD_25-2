"""
Pipeline de Facturación RIPS - Versión Modernizada

Pipeline automatizado con Prefect y PySpark para procesar facturas 
e historias electrónicas en salud (HEV) y generar archivos RIPS JSON 
según la normativa colombiana.
"""

__version__ = "1.0.0"
__author__ = "Pipeline RIPS Team"
__description__ = "Pipeline de facturación RIPS con Prefect y PySpark"

from .config.settings import PipelineConfig, get_config
from .pipeline.main_pipeline import rips_pipeline, rips_pipeline_batch
from .validation.rips_validator import RIPSValidator
from .processing.spark_processor import SparkRIPSProcessor

__all__ = [
    "PipelineConfig",
    "get_config", 
    "rips_pipeline",
    "rips_pipeline_batch",
    "RIPSValidator",
    "SparkRIPSProcessor"
]

