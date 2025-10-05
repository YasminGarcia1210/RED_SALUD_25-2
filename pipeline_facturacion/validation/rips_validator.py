"""
Validador robusto para archivos RIPS según normativa colombiana
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from pathlib import Path
import json

from ..config.settings import PipelineConfig
from ..utils.logger import setup_logger

@dataclass
class ValidationResult:
    """Resultado de validación con detalles"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data: Dict[str, Any]
    validation_timestamp: str
    file_name: Optional[str] = None

class RIPSValidator:
    """Validador principal para archivos RIPS"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = setup_logger("rips_validator", {
            "log_level": config.log_level,
            "log_format": config.log_format
        })
        
        # Códigos CUPS válidos para vacunación
        self.valid_cups_codes = {
            "993504": "VACUNACION CONTRA FIEBRE AMARILLA",
            "993510": "VACUNACION CONTRA INFLUENZA DOSIS UNICA OTRAS EDADES",
            "993130": "VACUNACION PENTAVALENTE 1 REFUERZO",
            "993501": "VACUNACION CONTRA POLIOMIELITIS IVP 1 REFUERZO",
            "993522": "VACUNACION SRP TRIPLE VIRAL MMR 1 REFUERZO",
            "995202": "VACUNA COVID 19 INTRAMURAL 1 REFUERZO",
            "993513": "VIRUS DE PAPILOMA HUMANO VPH NINOS",
            "993512": "VACUNACION CONTRA ROTAVIRUS 2 DOSIS"
        }
        
        # Tipos de documento válidos
        self.valid_document_types = ["CC", "TI", "RC", "AS", "MS", "PA", "PE"]
        
        # Códigos de sexo válidos
        self.valid_sex_codes = ["M", "F"]
        
        # Códigos de diagnóstico válidos (excluyendo Z00-Z99)
        self.invalid_diagnosis_prefixes = ["Z"]
    
    def validate_rips_file(self, rips_data: Dict[str, Any], file_name: str = None) -> ValidationResult:
        """
        Valida un archivo RIPS completo
        
        Args:
            rips_data: Datos del archivo RIPS
            file_name: Nombre del archivo (opcional)
            
        Returns:
            ValidationResult: Resultado de la validación
        """
        errors = []
        warnings = []
        
        self.logger.info(f"Iniciando validación de RIPS", file_name=file_name)
        
        # Validar estructura básica
        if not isinstance(rips_data, dict):
            errors.append("El archivo RIPS debe ser un objeto JSON válido")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                data=rips_data,
                validation_timestamp=datetime.now().isoformat(),
                file_name=file_name
            )
        
        # Validar campos obligatorios del RIPS
        required_rips_fields = ["numFactura", "numDocumentoIdObligado", "usuarios"]
        for field in required_rips_fields:
            if field not in rips_data:
                errors.append(f"Campo obligatorio faltante: {field}")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                data=rips_data,
                validation_timestamp=datetime.now().isoformat(),
                file_name=file_name
            )
        
        # Validar usuarios
        if not isinstance(rips_data["usuarios"], list) or len(rips_data["usuarios"]) == 0:
            errors.append("El campo 'usuarios' debe ser una lista no vacía")
        else:
            for i, usuario in enumerate(rips_data["usuarios"]):
                user_validation = self._validate_user(usuario, user_index=i)
                errors.extend(user_validation.errors)
                warnings.extend(user_validation.warnings)
        
        # Validar número de factura
        if not self._validate_factura_number(rips_data.get("numFactura")):
            errors.append("Número de factura inválido o faltante")
        
        # Validar NIT del obligado
        if not self._validate_nit(rips_data.get("numDocumentoIdObligado")):
            errors.append("NIT del obligado inválido o faltante")
        
        is_valid = len(errors) == 0
        
        self.logger.info(
            f"Validación completada",
            file_name=file_name,
            is_valid=is_valid,
            error_count=len(errors),
            warning_count=len(warnings)
        )
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            data=rips_data,
            validation_timestamp=datetime.now().isoformat(),
            file_name=file_name
        )
    
    def _validate_user(self, usuario: Dict[str, Any], user_index: int) -> ValidationResult:
        """Valida los datos de un usuario"""
        errors = []
        warnings = []
        
        # Validar campos obligatorios del usuario
        required_user_fields = [
            "tipoDocumentoIdentificacion",
            "numDocumentoIdentificacion",
            "fechaNacimiento",
            "codSexo",
            "servicios"
        ]
        
        for field in required_user_fields:
            if field not in usuario:
                errors.append(f"Usuario {user_index}: Campo obligatorio faltante: {field}")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                data=usuario,
                validation_timestamp=datetime.now().isoformat()
            )
        
        # Validar tipo de documento
        if not self._validate_document_type(usuario.get("tipoDocumentoIdentificacion")):
            errors.append(f"Usuario {user_index}: Tipo de documento inválido")
        
        # Validar número de documento
        if not self._validate_document_number(usuario.get("numDocumentoIdentificacion")):
            errors.append(f"Usuario {user_index}: Número de documento inválido")
        
        # Validar fecha de nacimiento
        if not self._validate_birth_date(usuario.get("fechaNacimiento")):
            errors.append(f"Usuario {user_index}: Fecha de nacimiento inválida")
        
        # Validar código de sexo
        if not self._validate_sex_code(usuario.get("codSexo")):
            errors.append(f"Usuario {user_index}: Código de sexo inválido")
        
        # Validar servicios
        if isinstance(usuario.get("servicios"), dict):
            services_validation = self._validate_services(usuario["servicios"], user_index)
            errors.extend(services_validation.errors)
            warnings.extend(services_validation.warnings)
        else:
            errors.append(f"Usuario {user_index}: Campo 'servicios' debe ser un objeto")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data=usuario,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _validate_services(self, servicios: Dict[str, Any], user_index: int) -> ValidationResult:
        """Valida los servicios del usuario"""
        errors = []
        warnings = []
        
        # Validar procedimientos
        if "procedimientos" in servicios:
            if not isinstance(servicios["procedimientos"], list):
                errors.append(f"Usuario {user_index}: 'procedimientos' debe ser una lista")
            else:
                for i, procedimiento in enumerate(servicios["procedimientos"]):
                    proc_validation = self._validate_procedure(procedimiento, user_index, i)
                    errors.extend(proc_validation.errors)
                    warnings.extend(proc_validation.warnings)
        else:
            warnings.append(f"Usuario {user_index}: No se encontraron procedimientos")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data=servicios,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _validate_procedure(self, procedimiento: Dict[str, Any], user_index: int, proc_index: int) -> ValidationResult:
        """Valida un procedimiento específico"""
        errors = []
        warnings = []
        
        # Validar campos obligatorios del procedimiento
        required_proc_fields = [
            "codProcedimiento",
            "vrServicio",
            "codServicio",
            "consecutivo",
            "codPrestador",
            "grupoServicios",
            "conceptoRecaudo",
            "valorPagoModerador",
            "fechaInicioAtencion",
            "codDiagnosticoPrincipal",
            "viaIngresoServicioSalud",
            "finalidadTecnologiaSalud",
            "numDocumentoIdentificacion",
            "tipoDocumentoIdentificacion",
            "modalidadGrupoServicioTecSal"
        ]
        
        for field in required_proc_fields:
            if field not in procedimiento:
                errors.append(f"Usuario {user_index}, Procedimiento {proc_index}: Campo obligatorio faltante: {field}")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                data=procedimiento,
                validation_timestamp=datetime.now().isoformat()
            )
        
        # Validar código CUPS
        if not self._validate_cups_code(procedimiento.get("codProcedimiento")):
            errors.append(f"Usuario {user_index}, Procedimiento {proc_index}: Código CUPS inválido")
        
        # Validar valor del servicio
        if not self._validate_service_value(procedimiento.get("vrServicio")):
            errors.append(f"Usuario {user_index}, Procedimiento {proc_index}: Valor del servicio inválido")
        
        # Validar diagnóstico principal
        if not self._validate_diagnosis(procedimiento.get("codDiagnosticoPrincipal")):
            errors.append(f"Usuario {user_index}, Procedimiento {proc_index}: Diagnóstico principal inválido")
        
        # Validar fecha de atención
        if not self._validate_attention_date(procedimiento.get("fechaInicioAtencion")):
            errors.append(f"Usuario {user_index}, Procedimiento {proc_index}: Fecha de atención inválida")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data=procedimiento,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _validate_factura_number(self, factura: str) -> bool:
        """Valida el número de factura"""
        if not factura:
            return False
        
        # Debe seguir el patrón FERO + 6 dígitos
        pattern = r"^FERO\d{6}$"
        return bool(re.match(pattern, str(factura)))
    
    def _validate_nit(self, nit: str) -> bool:
        """Valida el NIT del obligado"""
        if not nit:
            return False
        
        # Debe ser un número de 9-10 dígitos
        pattern = r"^\d{9,10}$"
        return bool(re.match(pattern, str(nit)))
    
    def _validate_document_type(self, doc_type: str) -> bool:
        """Valida el tipo de documento"""
        return doc_type in self.valid_document_types
    
    def _validate_document_number(self, doc_number: str) -> bool:
        """Valida el número de documento"""
        if not doc_number:
            return False
        
        # Debe ser un número de 6-15 dígitos
        pattern = r"^\d{6,15}$"
        return bool(re.match(pattern, str(doc_number)))
    
    def _validate_birth_date(self, birth_date: str) -> bool:
        """Valida la fecha de nacimiento"""
        if not birth_date:
            return False
        
        try:
            # Formato esperado: YYYY-MM-DD
            datetime.strptime(birth_date, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def _validate_sex_code(self, sex_code: str) -> bool:
        """Valida el código de sexo"""
        return sex_code in self.valid_sex_codes
    
    def _validate_cups_code(self, cups_code: str) -> bool:
        """Valida el código CUPS"""
        if not cups_code:
            return False
        
        # Debe ser un código válido de 6 dígitos
        pattern = r"^\d{6}$"
        if not re.match(pattern, str(cups_code)):
            return False
        
        # Verificar que esté en la lista de códigos válidos
        return cups_code in self.valid_cups_codes
    
    def _validate_service_value(self, value: Any) -> bool:
        """Valida el valor del servicio"""
        if value is None:
            return False
        
        try:
            float_value = float(value)
            return float_value > 0
        except (ValueError, TypeError):
            return False
    
    def _validate_diagnosis(self, diagnosis: str) -> bool:
        """Valida el código de diagnóstico"""
        if not diagnosis:
            return False
        
        # No debe empezar con Z (factores que influyen en el estado de salud)
        if diagnosis.startswith("Z"):
            return False
        
        # Debe ser un código alfanumérico de 3-10 caracteres
        pattern = r"^[A-Z0-9]{3,10}$"
        return bool(re.match(pattern, str(diagnosis)))
    
    def _validate_attention_date(self, attention_date: str) -> bool:
        """Valida la fecha de atención"""
        if not attention_date:
            return False
        
        try:
            # Formato esperado: YYYY-MM-DD HH:MM
            datetime.strptime(attention_date, "%Y-%m-%d %H:%M")
            return True
        except ValueError:
            return False
    
    def validate_batch(self, rips_files: List[Dict[str, Any]], file_names: List[str] = None) -> List[ValidationResult]:
        """
        Valida un lote de archivos RIPS
        
        Args:
            rips_files: Lista de datos de archivos RIPS
            file_names: Lista de nombres de archivos (opcional)
            
        Returns:
            List[ValidationResult]: Lista de resultados de validación
        """
        results = []
        
        self.logger.info(f"Iniciando validación de lote", file_count=len(rips_files))
        
        for i, rips_data in enumerate(rips_files):
            file_name = file_names[i] if file_names and i < len(file_names) else f"file_{i}"
            result = self.validate_rips_file(rips_data, file_name)
            results.append(result)
        
        # Calcular estadísticas
        valid_count = sum(1 for r in results if r.is_valid)
        error_count = sum(len(r.errors) for r in results)
        warning_count = sum(len(r.warnings) for r in results)
        
        self.logger.info(
            f"Validación de lote completada",
            total_files=len(rips_files),
            valid_files=valid_count,
            total_errors=error_count,
            total_warnings=warning_count
        )
        
        return results
    
    def generate_validation_report(self, results: List[ValidationResult], output_path: Path) -> Dict[str, Any]:
        """
        Genera un reporte de validación
        
        Args:
            results: Lista de resultados de validación
            output_path: Ruta donde guardar el reporte
            
        Returns:
            Dict[str, Any]: Resumen del reporte
        """
        total_files = len(results)
        valid_files = sum(1 for r in results if r.is_valid)
        invalid_files = total_files - valid_files
        
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        # Agrupar errores por tipo
        error_types = {}
        for result in results:
            for error in result.errors:
                error_type = error.split(":")[0] if ":" in error else "General"
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Crear reporte
        report = {
            "validation_summary": {
                "total_files": total_files,
                "valid_files": valid_files,
                "invalid_files": invalid_files,
                "success_rate": (valid_files / total_files * 100) if total_files > 0 else 0,
                "total_errors": total_errors,
                "total_warnings": total_warnings
            },
            "error_breakdown": error_types,
            "file_details": [
                {
                    "file_name": r.file_name,
                    "is_valid": r.is_valid,
                    "error_count": len(r.errors),
                    "warning_count": len(r.warnings),
                    "errors": r.errors,
                    "warnings": r.warnings
                }
                for r in results
            ],
            "validation_timestamp": datetime.now().isoformat()
        }
        
        # Guardar reporte
        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(
            f"Reporte de validación generado",
            report_file=str(report_file),
            success_rate=report["validation_summary"]["success_rate"]
        )
        
        return report

