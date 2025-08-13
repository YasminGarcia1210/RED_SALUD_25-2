"""
Ejemplo de uso del Pipeline de Facturación RIPS

Este script demuestra cómo usar el pipeline modernizado con Prefect y PySpark
"""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .pipeline.main_pipeline import rips_pipeline, rips_pipeline_batch
from .config.settings import get_config
from .validation.rips_validator import RIPSValidator

console = Console()

def example_basic_usage():
    """Ejemplo básico de uso del pipeline"""
    
    console.print(Panel.fit(
        "[bold blue]🚀 Ejemplo Básico - Pipeline RIPS[/bold blue]\n"
        "Ejecutando pipeline completo en modo desarrollo",
        title="Ejemplo 1: Uso Básico"
    ))
    
    try:
        # Ejecutar pipeline básico
        result = rips_pipeline(
            environment="development",
            enable_notifications=False
        )
        
        # Mostrar resultados
        console.print(f"[green]✅ Pipeline completado[/green]")
        console.print(f"Estado: {result['status']}")
        console.print(f"Tiempo: {result['processing_time']:.2f} segundos")
        
        if result['status'] == 'success':
            console.print(f"Archivos procesados: {result['input_files']}")
            console.print(f"Tasa de éxito: {result['validation_summary']['success_rate']:.1f}%")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

def example_batch_processing():
    """Ejemplo de procesamiento por lotes"""
    
    console.print(Panel.fit(
        "[bold blue]📦 Ejemplo - Procesamiento por Lotes[/bold blue]\n"
        "Ejecutando pipeline en modo lote con 50 archivos por lote",
        title="Ejemplo 2: Procesamiento por Lotes"
    ))
    
    try:
        # Ejecutar pipeline por lotes
        results = rips_pipeline_batch(
            batch_size=50,
            environment="development"
        )
        
        # Mostrar resultados
        console.print(f"[green]✅ Procesamiento por lotes completado[/green]")
        console.print(f"Total de lotes: {len(results)}")
        
        success_batches = sum(1 for r in results if r['status'] == 'success')
        console.print(f"Lotes exitosos: {success_batches}/{len(results)}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

def example_validation_only():
    """Ejemplo de validación de archivos RIPS existentes"""
    
    console.print(Panel.fit(
        "[bold blue]✅ Ejemplo - Validación de RIPS[/bold blue]\n"
        "Validando archivos RIPS existentes sin procesamiento",
        title="Ejemplo 3: Solo Validación"
    ))
    
    try:
        # Cargar configuración
        config = get_config("development")
        
        # Crear validador
        validator = RIPSValidator(config)
        
        # Buscar archivos RIPS
        rips_files = list(config.output_paths["rips"].glob("*_Rips.json"))
        
        if not rips_files:
            console.print("[yellow]⚠️ No se encontraron archivos RIPS para validar[/yellow]")
            return
        
        console.print(f"[green]📄 Encontrados {len(rips_files)} archivos RIPS[/green]")
        
        # Validar archivos
        import json
        results = []
        
        for rips_file in rips_files[:5]:  # Solo los primeros 5 para el ejemplo
            try:
                with open(rips_file, 'r', encoding='utf-8') as f:
                    rips_data = json.load(f)
                
                result = validator.validate_rips_file(rips_data, rips_file.name)
                results.append(result)
                
            except Exception as e:
                console.print(f"[red]❌ Error validando {rips_file.name}: {str(e)}[/red]")
        
        # Mostrar resultados
        valid_files = sum(1 for r in results if r.is_valid)
        total_errors = sum(len(r.errors) for r in results)
        
        console.print(f"[green]✅ Validación completada[/green]")
        console.print(f"Archivos válidos: {valid_files}/{len(results)}")
        console.print(f"Errores totales: {total_errors}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

def example_configuration():
    """Ejemplo de configuración del pipeline"""
    
    console.print(Panel.fit(
        "[bold blue]⚙️ Ejemplo - Configuración[/bold blue]\n"
        "Mostrando configuración del pipeline",
        title="Ejemplo 4: Configuración"
    ))
    
    try:
        # Cargar configuraciones
        dev_config = get_config("development")
        prod_config = get_config("production")
        
        console.print("[bold]Configuración de Desarrollo:[/bold]")
        console.print(f"  Tamaño de lote: {dev_config.batch_size}")
        console.print(f"  Nivel de log: {dev_config.log_level}")
        console.print(f"  Spark Master: {dev_config.spark.master}")
        
        console.print("\n[bold]Configuración de Producción:[/bold]")
        console.print(f"  Tamaño de lote: {prod_config.batch_size}")
        console.print(f"  Nivel de log: {prod_config.log_level}")
        console.print(f"  Spark Master: {prod_config.spark.master}")
        console.print(f"  Notificaciones: {prod_config.enable_notifications}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

def example_custom_processing():
    """Ejemplo de procesamiento personalizado"""
    
    console.print(Panel.fit(
        "[bold blue]🔧 Ejemplo - Procesamiento Personalizado[/bold blue]\n"
        "Usando componentes del pipeline de forma individual",
        title="Ejemplo 5: Procesamiento Personalizado"
    ))
    
    try:
        # Cargar configuración
        config = get_config("development")
        
        # Crear validador
        validator = RIPSValidator(config)
        
        # Datos de ejemplo para validación
        sample_rips_data = {
            "numFactura": "FERO123456",
            "numDocumentoIdObligado": "805027337",
            "usuarios": [
                {
                    "tipoDocumentoIdentificacion": "CC",
                    "numDocumentoIdentificacion": "12345678",
                    "fechaNacimiento": "1990-01-01",
                    "codSexo": "M",
                    "servicios": {
                        "procedimientos": [
                            {
                                "codProcedimiento": "993504",
                                "vrServicio": 9000.0,
                                "codServicio": "01",
                                "consecutivo": 1,
                                "codPrestador": "805027337",
                                "grupoServicios": "01",
                                "conceptoRecaudo": "01",
                                "valorPagoModerador": 0.0,
                                "fechaInicioAtencion": "2024-01-01 08:00",
                                "codDiagnosticoPrincipal": "A01",
                                "viaIngresoServicioSalud": "01",
                                "finalidadTecnologiaSalud": "01",
                                "numDocumentoIdentificacion": "12345678",
                                "tipoDocumentoIdentificacion": "CC",
                                "modalidadGrupoServicioTecSal": "01"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Validar datos de ejemplo
        result = validator.validate_rips_file(sample_rips_data, "ejemplo.json")
        
        console.print(f"[green]✅ Validación de ejemplo completada[/green]")
        console.print(f"Válido: {result.is_valid}")
        console.print(f"Errores: {len(result.errors)}")
        console.print(f"Advertencias: {len(result.warnings)}")
        
        if result.errors:
            console.print("[red]Errores encontrados:[/red]")
            for error in result.errors:
                console.print(f"  - {error}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

def main():
    """Función principal que ejecuta todos los ejemplos"""
    
    console.print(Panel.fit(
        "[bold blue]🎯 Pipeline de Facturación RIPS - Ejemplos de Uso[/bold blue]\n"
        "Demostración de las funcionalidades del pipeline modernizado",
        title="Ejemplos de Uso"
    ))
    
    # Ejecutar ejemplos
    examples = [
        ("Uso Básico", example_basic_usage),
        ("Procesamiento por Lotes", example_batch_processing),
        ("Solo Validación", example_validation_only),
        ("Configuración", example_configuration),
        ("Procesamiento Personalizado", example_custom_processing)
    ]
    
    for name, example_func in examples:
        console.print(f"\n[bold cyan]Ejecutando: {name}[/bold cyan]")
        try:
            example_func()
        except Exception as e:
            console.print(f"[red]Error en ejemplo '{name}': {str(e)}[/red]")
        
        console.print("\n" + "="*60)
    
    console.print(Panel.fit(
        "[bold green]✅ Todos los ejemplos completados[/bold green]\n"
        "Revisa los resultados y logs para más detalles",
        title="Finalización"
    ))

if __name__ == "__main__":
    main()

