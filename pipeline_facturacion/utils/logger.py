"""
Sistema de logging estructurado para el pipeline de facturación RIPS
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from datetime import datetime
import json
from prefect import get_run_logger

class StructuredLogger:
    """Logger estructurado con soporte para Prefect y archivos"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> structlog.BoundLogger:
        """Configura el logger estructurado"""
        
        # Configurar structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if self.config.get("log_format") == "json" 
                else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger(self.name)
    
    def info(self, message: str, **kwargs):
        """Log de información"""
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de error"""
        self.logger.error(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de advertencia"""
        self.logger.warning(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico"""
        self.logger.critical(message, **kwargs)

class PrefectLogger:
    """Logger específico para Prefect"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_run_logger()
    
    def info(self, message: str, **kwargs):
        """Log de información"""
        self.logger.info(f"[{self.name}] {message}", extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de error"""
        self.logger.error(f"[{self.name}] {message}", extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de advertencia"""
        self.logger.warning(f"[{self.name}] {message}", extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(f"[{self.name}] {message}", extra=kwargs)

class FileLogger:
    """Logger para archivos con rotación"""
    
    def __init__(self, name: str, log_file: Path, level: str = "INFO"):
        self.name = name
        self.log_file = log_file
        self.level = getattr(logging, level.upper())
        
        # Configurar logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Evitar duplicación de handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers del logger"""
        
        # Handler para archivo
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(self.level)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        
        # Formato estructurado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log de información"""
        self.logger.info(f"{message} {kwargs}")
    
    def error(self, message: str, **kwargs):
        """Log de error"""
        self.logger.error(f"{message} {kwargs}")
    
    def warning(self, message: str, **kwargs):
        """Log de advertencia"""
        self.logger.warning(f"{message} {kwargs}")
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(f"{message} {kwargs}")

def setup_logger(name: str, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """
    Configura y retorna un logger estructurado
    
    Args:
        name: Nombre del logger
        config: Configuración del logger
    
    Returns:
        StructuredLogger: Logger configurado
    """
    if config is None:
        config = {
            "log_level": "INFO",
            "log_format": "json"
        }
    
    return StructuredLogger(name, config)

def setup_prefect_logger(name: str) -> PrefectLogger:
    """
    Configura y retorna un logger para Prefect
    
    Args:
        name: Nombre del logger
    
    Returns:
        PrefectLogger: Logger de Prefect
    """
    return PrefectLogger(name)

def setup_file_logger(name: str, log_file: Path, level: str = "INFO") -> FileLogger:
    """
    Configura y retorna un logger para archivos
    
    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log
        level: Nivel de logging
    
    Returns:
        FileLogger: Logger de archivo
    """
    return FileLogger(name, log_file, level)

class MetricsLogger:
    """Logger especializado para métricas del pipeline"""
    
    def __init__(self, name: str, metrics_file: Path):
        self.name = name
        self.metrics_file = metrics_file
        self.logger = setup_logger(f"{name}_metrics")
    
    def log_metric(self, metric_name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """
        Registra una métrica
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            tags: Tags adicionales
        """
        metric_data = {
            "timestamp": datetime.now().isoformat(),
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {}
        }
        
        # Log estructurado
        self.logger.info("Pipeline metric", **metric_data)
        
        # Guardar en archivo de métricas
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metric_data) + '\n')
    
    def log_processing_time(self, operation: str, duration: float, file_count: int = 1):
        """Registra tiempo de procesamiento"""
        self.log_metric(
            "processing_time",
            duration,
            {"operation": operation, "file_count": str(file_count)}
        )
    
    def log_error_rate(self, total_files: int, error_files: int):
        """Registra tasa de error"""
        error_rate = (error_files / total_files) * 100 if total_files > 0 else 0
        self.log_metric(
            "error_rate",
            error_rate,
            {"total_files": str(total_files), "error_files": str(error_files)}
        )
    
    def log_success_rate(self, total_files: int, success_files: int):
        """Registra tasa de éxito"""
        success_rate = (success_files / total_files) * 100 if total_files > 0 else 0
        self.log_metric(
            "success_rate",
            success_rate,
            {"total_files": str(total_files), "success_files": str(success_files)}
        )

