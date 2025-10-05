"""
Interfaz de línea de comandos para el pipeline de facturación RIPS
"""
import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from .pipeline.main_pipeline import rips_pipeline, rips_pipeline_batch
from .config.settings import get_config
from .utils.logger import setup_logger

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Pipeline de facturación RIPS - Herramienta de línea de comandos"""
    pass

@cli.command()
@click.option(
    "--environment", 
    "-e", 
    default="development",
    type=click.Choice(["development", "production"]),
    help="Entorno de ejecución"
)
@click.option(
    "--notifications", 
    "-n", 
    is_flag=True,
    help="Habilitar notificaciones"
)
@click.option(
    "--output-format", 
    "-f", 
    default="table",
    type=click.Choice(["table", "json", "summary"]),
    help="Formato de salida"
)
def run(environment: str, notifications: bool, output_format: str):
    """Ejecuta el pipeline completo de procesamiento RIPS"""
    
    console.print(Panel.fit(
        f"[bold blue]🚀 Pipeline de Facturación RIPS[/bold blue]\n"
        f"Entorno: [green]{environment}[/green]\n"
        f"Notificaciones: [{'green' if notifications else 'red'}]{'Habilitadas' if notifications else 'Deshabilitadas'}[/]",
        title="Iniciando Pipeline"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Ejecutando pipeline...", total=None)
        
        try:
            # Ejecutar pipeline
            result = rips_pipeline(
                environment=environment,
                enable_notifications=notifications
            )
            
            progress.update(task, completed=True)
            
            # Mostrar resultados según formato
            if output_format == "json":
                console.print_json(json.dumps(result, indent=2, default=str))
            elif output_format == "summary":
                show_summary(result)
            else:
                show_results_table(result)
                
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")
            raise click.Abort()

@cli.command()
@click.option(
    "--batch-size", 
    "-b", 
    default=100,
    type=int,
    help="Tamaño del lote"
)
@click.option(
    "--environment", 
    "-e", 
    default="development",
    type=click.Choice(["development", "production"]),
    help="Entorno de ejecución"
)
def batch(batch_size: int, environment: str):
    """Ejecuta el pipeline en modo lote"""
    
    console.print(Panel.fit(
        f"[bold blue]📦 Pipeline por Lotes[/bold blue]\n"
        f"Tamaño de lote: [green]{batch_size}[/green]\n"
        f"Entorno: [green]{environment}[/green]",
        title="Iniciando Procesamiento por Lotes"
    ))
    
    try:
        # Ejecutar pipeline por lotes
        results = rips_pipeline_batch(
            batch_size=batch_size,
            environment=environment
        )
        
        # Mostrar resultados
        show_batch_results(results)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")
        raise click.Abort()

@cli.command()
@click.option(
    "--environment", 
    "-e", 
    default="development",
    type=click.Choice(["development", "production"]),
    help="Entorno de configuración"
)
def config(environment: str):
    """Muestra la configuración actual del pipeline"""
    
    try:
        config = get_config(environment)
        
        console.print(Panel.fit(
            f"[bold blue]⚙️ Configuración del Pipeline[/bold blue]\n"
            f"Entorno: [green]{environment}[/green]",
            title="Configuración Actual"
        ))
        
        # Crear tabla de configuración
        table = Table(title="Configuración del Pipeline")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="green")
        
        # Configuración básica
        table.add_row("Entorno", environment)
        table.add_row("Tamaño de lote", str(config.batch_size))
        table.add_row("Nivel de log", config.log_level)
        table.add_row("Formato de log", config.log_format)
        table.add_row("Reintentos máximos", str(config.max_retries))
        table.add_row("Timeout (segundos)", str(config.timeout_seconds))
        
        # Rutas de entrada
        table.add_row("", "")
        table.add_row("[bold]Rutas de Entrada[/bold]", "")
        table.add_row("HEV", str(config.input_paths["hev"]))
        table.add_row("XML", str(config.input_paths["xml"]))
        table.add_row("PDF", str(config.input_paths["pdf"]))
        
        # Rutas de salida
        table.add_row("", "")
        table.add_row("[bold]Rutas de Salida[/bold]", "")
        table.add_row("RIPS", str(config.output_paths["rips"]))
        table.add_row("Control", str(config.output_paths["control"]))
        table.add_row("Logs", str(config.output_paths["logs"]))
        
        # Configuración Spark
        table.add_row("", "")
        table.add_row("[bold]Configuración Spark[/bold]", "")
        table.add_row("App Name", config.spark.app_name)
        table.add_row("Master", config.spark.master)
        table.add_row("Driver Memory", config.spark.driver_memory)
        table.add_row("Executor Memory", config.spark.executor_memory)
        table.add_row("Max Workers", str(config.spark.max_workers))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error cargando configuración: {str(e)}[/bold red]")
        raise click.Abort()

@cli.command()
@click.option(
    "--path", 
    "-p", 
    default=".",
    help="Ruta del directorio a verificar"
)
def check(path: str):
    """Verifica la estructura de directorios y archivos"""
    
    console.print(Panel.fit(
        f"[bold blue]🔍 Verificación de Estructura[/bold blue]\n"
        f"Ruta: [green]{path}[/green]",
        title="Verificando Estructura"
    ))
    
    try:
        base_path = Path(path)
        
        # Verificar estructura
        structure_table = Table(title="Estructura de Directorios")
        structure_table.add_column("Directorio", style="cyan")
        structure_table.add_column("Estado", style="green")
        structure_table.add_column("Archivos", style="yellow")
        
        # Directorios requeridos
        required_dirs = [
            "input/fact_pdf",
            "input/fact_xml", 
            "input/hev",
            "output/rips",
            "control",
            "logs"
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            if full_path.exists():
                file_count = len(list(full_path.glob("*")))
                structure_table.add_row(
                    dir_path, 
                    "✅ Existe", 
                    str(file_count)
                )
            else:
                structure_table.add_row(
                    dir_path, 
                    "❌ No existe", 
                    "0"
                )
        
        console.print(structure_table)
        
        # Verificar archivos de entrada
        console.print("\n[bold]📁 Archivos de Entrada:[/bold]")
        
        input_table = Table()
        input_table.add_column("Tipo", style="cyan")
        input_table.add_column("Patrón", style="yellow")
        input_table.add_column("Encontrados", style="green")
        
        input_patterns = [
            ("HEV", "input/hev/*.pdf"),
            ("XML", "input/fact_xml/*.xml"),
            ("PDF", "input/fact_pdf/*.pdf")
        ]
        
        for file_type, pattern in input_patterns:
            files = list(base_path.glob(pattern))
            input_table.add_row(file_type, pattern, str(len(files)))
        
        console.print(input_table)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error verificando estructura: {str(e)}[/bold red]")
        raise click.Abort()

@cli.command()
@click.option(
    "--environment", 
    "-e", 
    default="development",
    type=click.Choice(["development", "production"]),
    help="Entorno de configuración"
)
def validate(environment: str):
    """Valida archivos RIPS existentes"""
    
    console.print(Panel.fit(
        f"[bold blue]✅ Validación de RIPS[/bold blue]\n"
        f"Entorno: [green]{environment}[/green]",
        title="Validando Archivos RIPS"
    ))
    
    try:
        config = get_config(environment)
        
        # Buscar archivos RIPS
        rips_files = list(config.output_paths["rips"].glob("*_Rips.json"))
        
        if not rips_files:
            console.print("[yellow]⚠️ No se encontraron archivos RIPS para validar[/yellow]")
            return
        
        console.print(f"[green]📄 Encontrados {len(rips_files)} archivos RIPS[/green]")
        
        # Validar archivos
        from .validation.rips_validator import RIPSValidator
        
        validator = RIPSValidator(config)
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Validando archivos...", total=len(rips_files))
            
            for rips_file in rips_files:
                try:
                    with open(rips_file, 'r', encoding='utf-8') as f:
                        rips_data = json.load(f)
                    
                    result = validator.validate_rips_file(rips_data, rips_file.name)
                    results.append(result)
                    
                except Exception as e:
                    console.print(f"[red]❌ Error validando {rips_file.name}: {str(e)}[/red]")
                
                progress.update(task, advance=1)
        
        # Mostrar resultados
        show_validation_results(results)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error en validación: {str(e)}[/bold red]")
        raise click.Abort()

def show_results_table(result: dict):
    """Muestra los resultados en formato tabla"""
    
    if result["status"] == "error":
        console.print(f"[bold red]❌ Pipeline falló: {result['error']}[/bold red]")
        return
    
    # Tabla de resumen
    summary_table = Table(title="Resumen del Pipeline")
    summary_table.add_column("Métrica", style="cyan")
    summary_table.add_column("Valor", style="green")
    
    summary_table.add_row("Estado", "✅ Exitoso" if result["status"] == "success" else "⚠️ Advertencia")
    summary_table.add_row("Tiempo de procesamiento", f"{result['processing_time']:.2f} segundos")
    summary_table.add_row("Archivos HEV", str(result["input_files"]["hev_count"]))
    summary_table.add_row("Archivos XML", str(result["input_files"]["xml_count"]))
    summary_table.add_row("Archivos PDF", str(result["input_files"]["pdf_count"]))
    
    if "validation_summary" in result:
        summary_table.add_row("Archivos RIPS generados", str(result["validation_summary"]["total_files"]))
        summary_table.add_row("Archivos válidos", str(result["validation_summary"]["valid_files"]))
        summary_table.add_row("Tasa de éxito", f"{result['validation_summary']['success_rate']:.1f}%")
        summary_table.add_row("Errores totales", str(result["validation_summary"]["total_errors"]))
        summary_table.add_row("Advertencias totales", str(result["validation_summary"]["total_warnings"]))
    
    console.print(summary_table)

def show_summary(result: dict):
    """Muestra un resumen simplificado"""
    
    if result["status"] == "error":
        console.print(f"[bold red]❌ Error: {result['error']}[/bold red]")
        return
    
    console.print(Panel.fit(
        f"[bold green]✅ Pipeline Completado[/bold green]\n"
        f"Tiempo: [yellow]{result['processing_time']:.2f}s[/yellow]\n"
        f"Archivos procesados: [blue]{result['input_files']['hev_count']} HEV, {result['input_files']['xml_count']} XML[/blue]\n"
        f"Tasa de éxito: [green]{result['validation_summary']['success_rate']:.1f}%[/green]",
        title="Resumen"
    ))

def show_batch_results(results: list):
    """Muestra los resultados del procesamiento por lotes"""
    
    # Tabla de resultados por lote
    batch_table = Table(title="Resultados por Lote")
    batch_table.add_column("Lote", style="cyan")
    batch_table.add_column("Estado", style="green")
    batch_table.add_column("Archivos", style="yellow")
    batch_table.add_column("Tasa de Éxito", style="blue")
    
    total_files = 0
    total_success = 0
    
    for result in results:
        batch_num = result["batch_number"]
        status = "✅ Exitoso" if result["status"] == "success" else "❌ Error"
        files = result.get("files_processed", 0)
        success_rate = result.get("validation_summary", {}).get("success_rate", 0)
        
        batch_table.add_row(
            str(batch_num),
            status,
            str(files),
            f"{success_rate:.1f}%" if success_rate > 0 else "N/A"
        )
        
        total_files += files
        if result["status"] == "success":
            total_success += files
    
    console.print(batch_table)
    
    # Resumen general
    overall_success_rate = (total_success / total_files * 100) if total_files > 0 else 0
    
    console.print(Panel.fit(
        f"[bold blue]📊 Resumen General[/bold blue]\n"
        f"Total de lotes: [green]{len(results)}[/green]\n"
        f"Total de archivos: [yellow]{total_files}[/yellow]\n"
        f"Tasa de éxito general: [green]{overall_success_rate:.1f}%[/green]",
        title="Resumen del Procesamiento por Lotes"
    ))

def show_validation_results(results: list):
    """Muestra los resultados de validación"""
    
    # Estadísticas
    total_files = len(results)
    valid_files = sum(1 for r in results if r.is_valid)
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    
    # Tabla de resumen
    summary_table = Table(title="Resumen de Validación")
    summary_table.add_column("Métrica", style="cyan")
    summary_table.add_column("Valor", style="green")
    
    summary_table.add_row("Total de archivos", str(total_files))
    summary_table.add_row("Archivos válidos", str(valid_files))
    summary_table.add_row("Archivos inválidos", str(total_files - valid_files))
    summary_table.add_row("Tasa de éxito", f"{(valid_files/total_files*100):.1f}%" if total_files > 0 else "0%")
    summary_table.add_row("Errores totales", str(total_errors))
    summary_table.add_row("Advertencias totales", str(total_warnings))
    
    console.print(summary_table)
    
    # Mostrar errores más comunes
    if total_errors > 0:
        error_counts = {}
        for result in results:
            for error in result.errors:
                error_type = error.split(":")[0] if ":" in error else "General"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        if error_counts:
            error_table = Table(title="Errores Más Comunes")
            error_table.add_column("Tipo de Error", style="red")
            error_table.add_column("Cantidad", style="yellow")
            
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                error_table.add_row(error_type, str(count))
            
            console.print(error_table)

if __name__ == "__main__":
    cli()

