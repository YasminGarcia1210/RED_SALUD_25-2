# 🚀 Pipeline de Facturación RIPS - Versión Modernizada

Pipeline automatizado con **Prefect** y **PySpark** para procesar facturas e historias electrónicas en salud (HEV) y generar archivos RIPS JSON según la normativa colombiana.

## ✨ Nuevas Características

### 🔧 **Arquitectura Modernizada**
- **Prefect**: Orquestación y monitoreo de flujos de trabajo
- **PySpark**: Procesamiento distribuido y escalable
- **Pydantic**: Configuración tipada y validación
- **Logging estructurado**: Trazabilidad completa del proceso

### 📊 **Funcionalidades Avanzadas**
- ✅ **Validación robusta** de archivos RIPS según normativa
- ✅ **Procesamiento distribuido** con PySpark
- ✅ **Monitoreo en tiempo real** con Prefect
- ✅ **CLI interactiva** con Rich para mejor UX
- ✅ **Reportes automáticos** de validación y métricas
- ✅ **Manejo de errores** y reintentos automáticos
- ✅ **Configuración centralizada** por entorno

## 🏗️ Arquitectura del Proyecto

```
pipeline_facturacion/
├── 📁 config/
│   └── settings.py              # Configuración centralizada
├── 📁 utils/
│   └── logger.py                # Sistema de logging estructurado
├── 📁 validation/
│   └── rips_validator.py        # Validador robusto de RIPS
├── 📁 processing/
│   └── spark_processor.py       # Procesador distribuido con PySpark
├── 📁 pipeline/
│   └── main_pipeline.py         # Pipeline principal con Prefect
├── 📁 input/
│   ├── fact_pdf/                # Facturas en PDF
│   ├── fact_xml/                # Facturas electrónicas XML
│   └── hev/                     # Historias clínicas electrónicas
├── 📁 output/
│   └── rips/                    # RIPS JSON generados
├── 📁 control/                  # Reportes de control
├── 📁 logs/                     # Logs estructurados
├── cli.py                       # Interfaz de línea de comandos
├── requirements.txt             # Dependencias actualizadas
└── README.md                    # Este archivo
```

## 🚀 Instalación y Configuración

### 1. **Instalar Dependencias**

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. **Configurar Variables de Entorno**

Crear archivo `.env` en la raíz del proyecto:

```env
# Configuración del pipeline
BATCH_SIZE=100
LOG_LEVEL=INFO
LOG_FORMAT=json
MAX_RETRIES=3
TIMEOUT_SECONDS=300

# Configuración de Spark
SPARK_APP_NAME=RIPS-Pipeline
SPARK_MASTER=local[*]
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_MAX_WORKERS=4

# Configuración de Prefect
PREFECT_API_URL=http://localhost:4200/api
PREFECT_PROJECT=rips-pipeline
PREFECT_WORK_QUEUE=rips-queue

# Notificaciones (opcional)
ENABLE_NOTIFICATIONS=false
NOTIFICATION_WEBHOOK=
```

### 3. **Preparar Estructura de Directorios**

```bash
# Crear directorios necesarios
mkdir -p input/fact_pdf input/fact_xml input/hev
mkdir -p output/rips control logs
```

## 🎯 Uso del Pipeline

### **Interfaz de Línea de Comandos (CLI)**

#### **Ejecutar Pipeline Completo**
```bash
# Ejecución básica
python -m pipeline_facturacion.cli run

# Con opciones avanzadas
python -m pipeline_facturacion.cli run \
  --environment production \
  --notifications \
  --output-format table
```

#### **Procesamiento por Lotes**
```bash
# Procesar en lotes de 50 archivos
python -m pipeline_facturacion.cli batch --batch-size 50
```

#### **Verificar Configuración**
```bash
# Mostrar configuración actual
python -m pipeline_facturacion.cli config --environment development
```

#### **Verificar Estructura**
```bash
# Verificar directorios y archivos
python -m pipeline_facturacion.cli check --path .
```

#### **Validar Archivos RIPS**
```bash
# Validar archivos RIPS existentes
python -m pipeline_facturacion.cli validate --environment development
```

### **Uso Programático**

```python
from pipeline_facturacion.pipeline.main_pipeline import rips_pipeline

# Ejecutar pipeline
result = rips_pipeline(
    environment="development",
    enable_notifications=False
)

print(f"Resultado: {result}")
```

## 📊 Flujo del Pipeline

### **1. Descubrimiento de Archivos**
- Escanea automáticamente las carpetas de entrada
- Valida existencia y formato de archivos
- Genera inventario de archivos a procesar

### **2. Procesamiento Distribuido**
- **PySpark**: Procesa archivos HEV y XML en paralelo
- **UDFs personalizadas**: Extracción de datos con regex optimizadas
- **Join distribuido**: Consolida información de múltiples fuentes

### **3. Validación Robusta**
- **Validación de estructura**: Campos obligatorios y tipos de datos
- **Validación de negocio**: Códigos CUPS, diagnósticos, fechas
- **Reportes detallados**: Errores y advertencias por archivo

### **4. Generación de RIPS**
- **Estructura JSON**: Conforme a normativa colombiana
- **Validación CUV**: Códigos únicos de validación
- **Archivos individuales**: Un RIPS por factura

### **5. Monitoreo y Reportes**
- **Métricas en tiempo real**: Tiempo de procesamiento, tasas de éxito
- **Logs estructurados**: Trazabilidad completa del proceso
- **Reportes automáticos**: Resúmenes y estadísticas

## 🔍 Validaciones Implementadas

### **Validaciones de Estructura**
- ✅ Campos obligatorios del RIPS
- ✅ Tipos de datos correctos
- ✅ Estructura JSON válida

### **Validaciones de Negocio**
- ✅ Número de factura (formato FERO + 6 dígitos)
- ✅ NIT del obligado (9-10 dígitos)
- ✅ Tipos de documento válidos (CC, TI, RC, etc.)
- ✅ Códigos CUPS válidos para vacunación
- ✅ Diagnósticos (excluyendo Z00-Z99)
- ✅ Fechas en formato correcto
- ✅ Valores de servicios > 0

### **Validaciones de Calidad**
- ✅ Detección de inasistencias
- ✅ Coherencia entre facturas y registros clínicos
- ✅ Validación de servicios prestados

## 📈 Métricas y Monitoreo

### **Métricas Automáticas**
- **Tiempo de procesamiento** por archivo y lote
- **Tasa de éxito** de validación
- **Tasa de error** por tipo de error
- **Throughput** de archivos por minuto

### **Reportes Generados**
- `summary_report_YYYYMMDD_HHMMSS.json`: Resumen del procesamiento
- `metrics_report_YYYYMMDD_HHMMSS.json`: Métricas detalladas
- `validation_report_YYYYMMDD_HHMMSS.json`: Resultados de validación

## 🛠️ Configuración Avanzada

### **Configuración de Spark**
```python
# En .env o variables de entorno
SPARK_MASTER=yarn                    # Para cluster
SPARK_DRIVER_MEMORY=4g              # Más memoria para procesamiento
SPARK_EXECUTOR_MEMORY=4g
SPARK_MAX_WORKERS=8                 # Más workers para paralelismo
```

### **Configuración de Prefect**
```python
# Habilitar UI de Prefect
prefect server start

# Configurar work queue
prefect work-queue create rips-queue
```

### **Configuración de Logging**
```python
# Logs en formato JSON para análisis
LOG_FORMAT=json
LOG_LEVEL=DEBUG  # Para desarrollo
LOG_LEVEL=WARNING  # Para producción
```

## 🧪 Testing y Validación

### **Ejecutar Tests**
```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio

# Ejecutar tests
pytest tests/
```

### **Validar Archivos de Ejemplo**
```bash
# Validar archivos RIPS existentes
python -m pipeline_facturacion.cli validate

# Verificar estructura
python -m pipeline_facturacion.cli check
```

## 📋 Tareas Pendientes y Mejoras

### **Mejoras Implementadas** ✅
- [x] Arquitectura con Prefect y PySpark
- [x] Configuración centralizada con Pydantic
- [x] Logging estructurado
- [x] Validación robusta de RIPS
- [x] CLI interactiva con Rich
- [x] Procesamiento distribuido
- [x] Reportes automáticos
- [x] Manejo de errores mejorado

### **Próximas Mejoras** 🔄
- [ ] **Integración con bases de datos**: PostgreSQL/MongoDB
- [ ] **API REST**: Endpoints para monitoreo
- [ ] **Dashboard web**: Interfaz gráfica
- [ ] **Notificaciones avanzadas**: Email, Slack, Teams
- [ ] **CI/CD**: Pipeline de despliegue automatizado
- [ ] **Tests unitarios**: Cobertura completa
- [ ] **Documentación API**: OpenAPI/Swagger

## 🆘 Solución de Problemas

### **Errores Comunes**

#### **Error: No se encuentran archivos**
```bash
# Verificar estructura
python -m pipeline_facturacion.cli check

# Verificar archivos en carpetas de entrada
ls input/hev/
ls input/fact_xml/
```

#### **Error: Spark no inicia**
```bash
# Verificar configuración de Spark
python -m pipeline_facturacion.cli config

# Usar configuración local
export SPARK_MASTER=local[*]
```

#### **Error: Prefect no conecta**
```bash
# Iniciar servidor Prefect
prefect server start

# Verificar configuración
python -m pipeline_facturacion.cli config
```

### **Logs y Debugging**
```bash
# Ver logs en tiempo real
tail -f logs/pipeline.log

# Cambiar nivel de log
export LOG_LEVEL=DEBUG
```

## 📞 Soporte

### **Comandos de Ayuda**
```bash
# Ayuda general
python -m pipeline_facturacion.cli --help

# Ayuda específica
python -m pipeline_facturacion.cli run --help
python -m pipeline_facturacion.cli validate --help
```

### **Información del Sistema**
```bash
# Verificar configuración
python -m pipeline_facturacion.cli config

# Verificar estructura
python -m pipeline_facturacion.cli check
```

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---
