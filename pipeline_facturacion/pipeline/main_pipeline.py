"""
Pipeline principal con Prefect para el procesamiento de facturación RIPS
"""
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.blocks.system import Secret
from prefect.filesystems import LocalFileSystem
from datetime import timedelta
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import glob

from ..config.settings import PipelineConfig, get_config
from ..utils.logger import setup_prefect_logger, MetricsLogger
from ..validation.rips_validator import RIPSValidator
from ..processing.spark_processor import SparkRIPSProcessor

@task(
    name="load_configuration",
    description="Carga la configuración del pipeline",
    retries=2,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
def load_configuration(environment: str = "development") -> PipelineConfig:
    """
    Carga la configuración del pipeline según el entorno
    
    Args:
        environment: Entorno de ejecución (development/production)
        
    Returns:
        PipelineConfig: Configuración cargada
    """
    logger = get_run_logger()
    logger.info(f"Cargando configuración para entorno: {environment}")
    
    try:
        config = get_config(environment)
        logger.info("Configuración cargada exitosamente", config_summary=config.dict())
        return config
    except Exception as e:
        logger.error(f"Error cargando configuración: {str(e)}")
        raise

@task(
    name="discover_input_files",
    description="Descubre archivos de entrada en las carpetas configuradas",
    retries=3,
    retry_delay_seconds=10
)
def discover_input_files(config: PipelineConfig) -> Dict[str, List[str]]:
    """
    Descubre archivos de entrada en las carpetas configuradas
    
    Args:
        config: Configuración del pipeline
        
    Returns:
        Dict[str, List[str]]: Diccionario con rutas de archivos por tipo
    """
    logger = get_run_logger()
    logger.info("Descubriendo archivos de entrada")
    
    input_files = {}
    
    try:
        # Descubrir archivos HEV
        hev_pattern = str(config.input_paths["hev"] / "*.pdf")
        hev_files = glob.glob(hev_pattern)
        input_files["hev"] = hev_files
        
        # Descubrir archivos XML
        xml_pattern = str(config.input_paths["xml"] / "*.xml")
        xml_files = glob.glob(xml_pattern)
        input_files["xml"] = xml_files
        
        # Descubrir archivos PDF
        pdf_pattern = str(config.input_paths["pdf"] / "*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        input_files["pdf"] = pdf_files
        
        logger.info(
            "Archivos descubiertos",
            hev_count=len(hev_files),
            xml_count=len(xml_files),
            pdf_count=len(pdf_files)
        )
        
        return input_files
        
    except Exception as e:
        logger.error(f"Error descubriendo archivos: {str(e)}")
        raise

@task(
    name="validate_input_files",
    description="Valida que los archivos de entrada sean válidos",
    retries=2,
    retry_delay_seconds=15
)
def validate_input_files(input_files: Dict[str, List[str]], config: PipelineConfig) -> Dict[str, List[str]]:
    """
    Valida que los archivos de entrada sean válidos
    
    Args:
        input_files: Diccionario con rutas de archivos
        config: Configuración del pipeline
        
    Returns:
        Dict[str, List[str]]: Diccionario con archivos válidos
    """
    logger = get_run_logger()
    logger.info("Validando archivos de entrada")
    
    valid_files = {}
    
    try:
        for file_type, files in input_files.items():
            valid_files[file_type] = []
            
            for file_path in files:
                file_path_obj = Path(file_path)
                
                # Verificar que el archivo existe y tiene tamaño > 0
                if file_path_obj.exists() and file_path_obj.stat().st_size > 0:
                    valid_files[file_type].append(file_path)
                else:
                    logger.warning(f"Archivo inválido: {file_path}")
        
        logger.info(
            "Validación completada",
            valid_hev=len(valid_files.get("hev", [])),
            valid_xml=len(valid_files.get("xml", [])),
            valid_pdf=len(valid_files.get("pdf", []))
        )
        
        return valid_files
        
    except Exception as e:
        logger.error(f"Error validando archivos: {str(e)}")
        raise

@task(
    name="process_with_spark",
    description="Procesa archivos usando PySpark",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=3600
)
def process_with_spark(
    hev_files: List[str], 
    xml_files: List[str], 
    config: PipelineConfig
) -> str:
    """
    Procesa archivos usando PySpark
    
    Args:
        hev_files: Lista de archivos HEV
        xml_files: Lista de archivos XML
        config: Configuración del pipeline
        
    Returns:
        str: Ruta del directorio de salida
    """
    logger = get_run_logger()
    logger.info("Iniciando procesamiento con PySpark")
    
    try:
        # Crear procesador Spark
        spark_processor = SparkRIPSProcessor(config)
        
        # Definir ruta de salida
        output_path = config.output_paths["rips"]
        
        # Procesar pipeline
        spark_processor.process_pipeline(hev_files, xml_files, output_path)
        
        # Detener Spark
        spark_processor.stop()
        
        logger.info("Procesamiento con PySpark completado", output_path=str(output_path))
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error en procesamiento Spark: {str(e)}")
        raise

@task(
    name="validate_generated_rips",
    description="Valida los archivos RIPS generados",
    retries=2,
    retry_delay_seconds=30
)
def validate_generated_rips(output_path: str, config: PipelineConfig) -> Dict[str, Any]:
    """
    Valida los archivos RIPS generados
    
    Args:
        output_path: Ruta del directorio de salida
        config: Configuración del pipeline
        
    Returns:
        Dict[str, Any]: Resultado de la validación
    """
    logger = get_run_logger()
    logger.info("Validando archivos RIPS generados")
    
    try:
        # Crear validador
        validator = RIPSValidator(config)
        
        # Cargar archivos RIPS
        rips_files = []
        rips_file_names = []
        
        output_path_obj = Path(output_path)
        for rips_file in output_path_obj.glob("*_Rips.json"):
            try:
                with open(rips_file, 'r', encoding='utf-8') as f:
                    rips_data = json.load(f)
                    rips_files.append(rips_data)
                    rips_file_names.append(rips_file.name)
            except Exception as e:
                logger.warning(f"Error cargando archivo RIPS {rips_file}: {str(e)}")
        
        # Validar archivos
        validation_results = validator.validate_batch(rips_files, rips_file_names)
        
        # Generar reporte
        report = validator.generate_validation_report(
            validation_results, 
            config.output_paths["control"]
        )
        
        logger.info(
            "Validación completada",
            total_files=report["validation_summary"]["total_files"],
            valid_files=report["validation_summary"]["valid_files"],
            success_rate=report["validation_summary"]["success_rate"]
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error validando RIPS: {str(e)}")
        raise

@task(
    name="generate_control_reports",
    description="Genera reportes de control",
    retries=2,
    retry_delay_seconds=20
)
def generate_control_reports(
    input_files: Dict[str, List[str]], 
    validation_report: Dict[str, Any], 
    config: PipelineConfig
) -> Dict[str, str]:
    """
    Genera reportes de control
    
    Args:
        input_files: Archivos de entrada
        validation_report: Reporte de validación
        config: Configuración del pipeline
        
    Returns:
        Dict[str, str]: Rutas de los reportes generados
    """
    logger = get_run_logger()
    logger.info("Generando reportes de control")
    
    try:
        report_paths = {}
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Reporte de resumen
        summary_report = {
            "timestamp": timestamp,
            "input_files": {
                "hev_count": len(input_files.get("hev", [])),
                "xml_count": len(input_files.get("xml", [])),
                "pdf_count": len(input_files.get("pdf", []))
            },
            "validation_summary": validation_report["validation_summary"],
            "processing_status": "completed"
        }
        
        summary_path = config.output_paths["control"] / f"summary_report_{timestamp}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2)
        
        report_paths["summary"] = str(summary_path)
        
        # Reporte de métricas
        metrics_report = {
            "timestamp": timestamp,
            "processing_metrics": {
                "total_input_files": sum(len(files) for files in input_files.values()),
                "success_rate": validation_report["validation_summary"]["success_rate"],
                "error_rate": 100 - validation_report["validation_summary"]["success_rate"]
            }
        }
        
        metrics_path = config.output_paths["control"] / f"metrics_report_{timestamp}.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_report, f, ensure_ascii=False, indent=2)
        
        report_paths["metrics"] = str(metrics_path)
        
        logger.info("Reportes de control generados", report_count=len(report_paths))
        return report_paths
        
    except Exception as e:
        logger.error(f"Error generando reportes: {str(e)}")
        raise

@task(
    name="send_notifications",
    description="Envía notificaciones sobre el resultado del pipeline",
    retries=2,
    retry_delay_seconds=30
)
def send_notifications(
    validation_report: Dict[str, Any], 
    control_reports: Dict[str, str], 
    config: PipelineConfig
) -> bool:
    """
    Envía notificaciones sobre el resultado del pipeline
    
    Args:
        validation_report: Reporte de validación
        control_reports: Reportes de control
        config: Configuración del pipeline
        
    Returns:
        bool: True si las notificaciones se enviaron exitosamente
    """
    logger = get_run_logger()
    
    if not config.enable_notifications:
        logger.info("Notificaciones deshabilitadas")
        return True
    
    try:
        # Aquí se implementaría la lógica de notificación
        # Por ejemplo, enviar email, webhook, etc.
        
        success_rate = validation_report["validation_summary"]["success_rate"]
        
        if success_rate >= 95:
            logger.info("Pipeline completado exitosamente", success_rate=success_rate)
        elif success_rate >= 80:
            logger.warning("Pipeline completado con advertencias", success_rate=success_rate)
        else:
            logger.error("Pipeline completado con errores", success_rate=success_rate)
        
        return True
        
    except Exception as e:
        logger.error(f"Error enviando notificaciones: {str(e)}")
        return False

@flow(
    name="rips-pipeline",
    description="Pipeline principal para procesamiento de facturación RIPS",
    version="1.0.0",
    retries=1,
    retry_delay_seconds=300
)
def rips_pipeline(
    environment: str = "development",
    enable_notifications: bool = False
) -> Dict[str, Any]:
    """
    Pipeline principal para procesamiento de facturación RIPS
    
    Args:
        environment: Entorno de ejecución (development/production)
        enable_notifications: Habilitar notificaciones
        
    Returns:
        Dict[str, Any]: Resultado del pipeline
    """
    logger = get_run_logger()
    logger.info("Iniciando pipeline de facturación RIPS", environment=environment)
    
    start_time = time.time()
    
    try:
        # 1. Cargar configuración
        config = load_configuration(environment)
        config.enable_notifications = enable_notifications
        
        # 2. Descubrir archivos de entrada
        input_files = discover_input_files(config)
        
        # 3. Validar archivos de entrada
        valid_files = validate_input_files(input_files, config)
        
        # Verificar que hay archivos para procesar
        if not valid_files.get("hev") or not valid_files.get("xml"):
            logger.warning("No hay suficientes archivos válidos para procesar")
            return {
                "status": "warning",
                "message": "No hay suficientes archivos válidos para procesar",
                "processing_time": time.time() - start_time
            }
        
        # 4. Procesar con PySpark
        output_path = process_with_spark(valid_files["hev"], valid_files["xml"], config)
        
        # 5. Validar archivos RIPS generados
        validation_report = validate_generated_rips(output_path, config)
        
        # 6. Generar reportes de control
        control_reports = generate_control_reports(valid_files, validation_report, config)
        
        # 7. Enviar notificaciones
        notifications_sent = send_notifications(validation_report, control_reports, config)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # Resultado final
        result = {
            "status": "success",
            "processing_time": processing_time,
            "input_files": {
                "hev_count": len(valid_files.get("hev", [])),
                "xml_count": len(valid_files.get("xml", [])),
                "pdf_count": len(valid_files.get("pdf", []))
            },
            "validation_summary": validation_report["validation_summary"],
            "output_path": output_path,
            "control_reports": control_reports,
            "notifications_sent": notifications_sent
        }
        
        logger.info(
            "Pipeline completado exitosamente",
            processing_time=processing_time,
            success_rate=validation_report["validation_summary"]["success_rate"]
        )
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error en pipeline: {str(e)}", processing_time=processing_time)
        
        return {
            "status": "error",
            "error": str(e),
            "processing_time": processing_time
        }

@flow(
    name="rips-pipeline-batch",
    description="Pipeline para procesamiento por lotes",
    version="1.0.0"
)
def rips_pipeline_batch(
    batch_size: int = 100,
    environment: str = "development"
) -> List[Dict[str, Any]]:
    """
    Pipeline para procesamiento por lotes
    
    Args:
        batch_size: Tamaño del lote
        environment: Entorno de ejecución
        
    Returns:
        List[Dict[str, Any]]: Resultados de los lotes
    """
    logger = get_run_logger()
    logger.info("Iniciando pipeline por lotes", batch_size=batch_size)
    
    # Cargar configuración
    config = load_configuration(environment)
    
    # Descubrir todos los archivos
    input_files = discover_input_files(config)
    valid_files = validate_input_files(input_files, config)
    
    hev_files = valid_files.get("hev", [])
    xml_files = valid_files.get("xml", [])
    
    # Procesar en lotes
    results = []
    
    for i in range(0, len(hev_files), batch_size):
        batch_hev = hev_files[i:i + batch_size]
        batch_xml = xml_files[i:i + batch_size]
        
        logger.info(f"Procesando lote {i//batch_size + 1}", batch_size=len(batch_hev))
        
        try:
            # Procesar lote
            output_path = process_with_spark(batch_hev, batch_xml, config)
            validation_report = validate_generated_rips(output_path, config)
            
            results.append({
                "batch_number": i//batch_size + 1,
                "status": "success",
                "files_processed": len(batch_hev),
                "validation_summary": validation_report["validation_summary"]
            })
            
        except Exception as e:
            logger.error(f"Error en lote {i//batch_size + 1}: {str(e)}")
            results.append({
                "batch_number": i//batch_size + 1,
                "status": "error",
                "error": str(e)
            })
    
    logger.info("Pipeline por lotes completado", total_batches=len(results))
    return results

if __name__ == "__main__":
    # Ejecutar pipeline
    result = rips_pipeline(environment="development", enable_notifications=False)
    print(f"Resultado del pipeline: {result}")

