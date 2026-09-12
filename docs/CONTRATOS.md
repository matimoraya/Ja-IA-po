# Contratos v0 — propuesta para congelar antes de implementar

Estos son contratos del proyecto a construir, no APIs existentes ni funciones de un proveedor. Mati centraliza cambios para que los cuatro frentes encajen.

## Datos

`data/scenarios/<scenario_id>/scenario.json` contiene `id`, `title`, `description`, `synthetic: true`, `events`, `processes`, `connections` y `deployments`. IDs públicos neutrales: `scenario-a`, `scenario-b`; los títulos no deben revelar al agente la respuesta esperada.

Evento: `id`, `timestamp` ISO 8601 con zona, `host`, `source`, `event_type`, `message`, y campos opcionales `user`, `ip`, `pid`. Proceso: `pid`, `host`, `user`, `command`, `parent_pid`, `started_at`, `event_ids`. Conexión: `id`, `host`, `pid`, `remote_ip`, `remote_port`, `timestamp`, `event_ids`. Deployment: `id`, `host`, `timestamp`, `description`, `event_ids`.

Usar IDs únicos por escenario. No incluir etiquetas de culpabilidad ni soluciones esperadas en los datos cargados por el agente. Los fixtures de evaluación viven fuera de data/scenarios.

## Herramientas internas (Python async)

Todas retornan `{ok: bool, data: object, error: null | {code: str, message: str}}`. Errores sin secretos. El backend inyecta `scenario_id` desde la investigación; el modelo no puede cambiar el escenario.

| Función | Argumentos elegibles por el modelo | Resultado principal en data |
|---|---|---|
| `search_logs` | `query`, `start?`, `end?`, `ip?`, `limit=50` | `events`, `truncated` |
| `get_timeline` | `start?`, `end?`, `limit=100` | `events` ordenados, `truncated` |
| `inspect_process` | `host`, `pid` | `process`, `events`, `connections` |
| `get_connections` | `host?`, `pid?` | `connections` |
| `get_recent_deployments` | `host?`, `start?`, `end?` | `deployments` |
| `research_security_context` | `query` público | `sources: [{id,title,url,excerpt}]`, `provider: "exa"` |

El host evita colisiones de PID. Filtros inválidos producen error explícito; resultados vacíos son éxito sin datos. Limitar tamaño y rango de consultas. No exponer shell, SQL arbitrario o lectura fuera del directorio del escenario.

Exa busca referencias sobre técnicas y mitigaciones, con hasta 3 fuentes por consulta y máximo propuesto de 2 consultas por investigación. Confirmar esquema del proveedor con su [documentación Search](https://exa.ai/docs/reference/search) antes de programar. La evidencia local prueba hechos del escenario; una página web solo aporta contexto público.

## Agente

Interfaz propuesta: `async run_investigation(scenario_id, objective, emit) -> report`. `emit` es un callback async que recibe eventos de actividad. Inyectar herramientas mediante un registro para probar con fixtures. Configuración inicial: hasta 10 rondas, 20 llamadas de herramientas totales y 90 segundos por investigación; los timeouts del proveedor deben respetar el tiempo restante. Al agotar presupuesto, devolver informe parcial `inconclusive`.

Actividad: `{id, timestamp, type, message, tool_name?, evidence_ids?}`. Tipos: `started`, `tool_started`, `tool_completed`, `tool_failed`, `finding`, `completed`, `failed`. Texto breve sobre acciones y resultados observables; no pedir ni revelar cadena de pensamiento.

Reporte: `{investigation_id, scenario_id, classification, severity, summary, timeline, findings, sources, recommendations, limitations, synthetic: true}`.

- classification: `incident | benign | inconclusive`.
- severity: `info | low | medium | high | critical`; severidad y certeza no son lo mismo.
- timeline: lista de `{timestamp, description, evidence_ids}`.
- findings: lista de `{id, statement, evidence_ids, source_ids}`.
- recommendations: lista de `{action, rationale, evidence_ids, source_ids}`.
- limitations: lista de faltantes, fallos de proveedor y alcance de los datos.

El backend valida que los IDs citados existen y las URLs vienen de resultados reales. Reportes inválidos no se muestran como éxito silencioso. Hallazgos vacíos y datos insuficientes son resultados válidos si se explican.

## HTTP de la aplicación

- `GET /api/scenarios` → `{scenarios:[{id,title,description,synthetic}]}`.
- `POST /api/investigations` con `{scenario_id, objective}` → 202 `{id,status:"queued"}`. Rechazar escenarios desconocidos con 404 y argumentos inválidos con 422.
- `GET /api/investigations/{id}` → `{id,status,activity,report,error}`. `status`: `queued | running | completed | failed`; report null hasta que exista, error null salvo fallo. ID desconocido: 404.
- `GET /api/investigations/{id}/report.md` → Markdown cuando terminó; 409 si aún no hay reporte, 404 si no existe.

UI consulta cada segundo y detiene polling al finalizar. Un proceso backend para la demo con almacenamiento en memoria; al reiniciar se pierden investigaciones. Indicar esa limitación. Una investigación activa a la vez; retornar 409 si ya hay otra. Ninguna clave de API llega al navegador.

