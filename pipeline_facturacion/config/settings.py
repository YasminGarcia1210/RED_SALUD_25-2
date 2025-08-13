"""
Configuración centralizada del pipeline de facturación RIPS
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DatabaseConfig(BaseModel):
    """Configuración de base de datos"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="rips_pipeline", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")

class SparkConfig(BaseModel):
    """Configuración de PySpark"""
    app_name: str = Field(default="RIPS-Pipeline", env="SPARK_APP_NAME")
    master: str = Field(default="local[*]", env="SPARK_MASTER")
    driver_memory: str = Field(default="2g", env="SPARK_DRIVER_MEMORY")
    executor_memory: str = Field(default="2g", env="SPARK_EXECUTOR_MEMORY")
    max_workers: int = Field(default=4, env="SPARK_MAX_WORKERS")

class PrefectConfig(BaseModel):
    """Configuración de Prefect"""
    api_url: str = Field(default="http://localhost:4200/api", env="PREFECT_API_URL")
    project_name: str = Field(default="rips-pipeline", env="PREFECT_PROJECT")
    work_queue_name: str = Field(default="rips-queue", env="PREFECT_WORK_QUEUE")

class ValidationConfig(BaseModel):
    """Configuración de validación"""
    required_fields: List[str] = Field(default=[
        "numDocumentoIdentificacion",
        "tipoDocumentoIdentificacion", 
        "fechaNacimiento",
        "codSexo",
        "codProcedimiento",
        "codDiagnosticoPrincipal"
    ])
    
    cups_codes: List[str] = Field(default=[
        "993504", "993510", "993130", "993501", "993522", "995202"
    ])
    
    valid_document_types: List[str] = Field(default=[
        "CC", "TI", "RC", "AS", "MS", "PA", "PE"
    ])

class PipelineConfig(BaseModel):
    """Configuración principal del pipeline"""
    
    # Rutas base
    base_path: Path = Field(default=Path(__file__).parent.parent)
    
    # Rutas de entrada
    input_pdf_path: Path = Field(default=Path("input/fact_pdf"))
    input_xml_path: Path = Field(default=Path("input/fact_xml"))
    input_hev_path: Path = Path("input/hev")
    
    # Rutas de salida
    output_rips_path: Path = Field(default=Path("output/rips"))
    output_control_path: Path = Field(default=Path("control"))
    output_logs_path: Path = Field(default=Path("logs"))
    
    # Configuración de procesamiento
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    timeout_seconds: int = Field(default=300, env="TIMEOUT_SECONDS")
    
    # Configuraciones específicas
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    spark: SparkConfig = Field(default_factory=SparkConfig)
    prefect: PrefectConfig = Field(default_factory=PrefectConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    
    # Configuración de logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Configuración de notificaciones
    enable_notifications: bool = Field(default=False, env="ENABLE_NOTIFICATIONS")
    notification_webhook: Optional[str] = Field(default=None, env="NOTIFICATION_WEBHOOK")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Crea los directorios necesarios si no existen"""
        directories = [
            self.base_path / self.input_pdf_path,
            self.base_path / self.input_xml_path,
            self.base_path / self.input_hev_path,
            self.base_path / self.output_rips_path,
            self.base_path / self.output_control_path,
            self.base_path / self.output_logs_path,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def input_paths(self) -> Dict[str, Path]:
        """Retorna un diccionario con todas las rutas de entrada"""
        return {
            "pdf": self.base_path / self.input_pdf_path,
            "xml": self.base_path / self.input_xml_path,
            "hev": self.base_path / self.input_hev_path,
        }
    
    @property
    def output_paths(self) -> Dict[str, Path]:
        """Retorna un diccionario con todas las rutas de salida"""
        return {
            "rips": self.base_path / self.output_rips_path,
            "control": self.base_path / self.output_control_path,
            "logs": self.base_path / self.output_logs_path,
        }

# Instancia global de configuración
config = PipelineConfig()

# Configuración específica para desarrollo
class DevelopmentConfig(PipelineConfig):
    """Configuración para desarrollo"""
    log_level: str = "DEBUG"
    batch_size: int = 10
    spark_master: str = "local[2]"

# Configuración específica para producción
class ProductionConfig(PipelineConfig):
    """Configuración para producción"""
    log_level: str = "WARNING"
    batch_size: int = 500
    enable_notifications: bool = True
    spark_master: str = "yarn"

def get_config(environment: str = "development") -> PipelineConfig:
    """Retorna la configuración según el entorno"""
    if environment == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()

