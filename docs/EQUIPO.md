# Organización del equipo

Fecha: 12 de septiembre de 2026. Límite indicado por Manu: 15:30. El horario de abajo usa provisionalmente America/Asuncion, zona de su máquina; sede y zona del plazo oficial aún deben confirmarse. No es una verificación del calendario del organizador.

## Responsables confirmados

Asignación actualizada por Manu. Cada persona usa su propia sesión de Codex; una sola persona integra cambios compartidos.

| Persona | Resultado a entregar | Archivos propios | Rama sugerida |
|---|---|---|---|
| Juan | Agente, registro y selección de herramientas, límites e informe estructurado | `app/agent/`, `tests/test_agent.py` | `feat/agent` |
| Elías | Dos escenarios sintéticos coherentes y resultados esperados | `data/scenarios/`, `tests/fixtures/`, `tests/test_scenarios.py` | `feat/scenarios` |
| Manu | Herramientas locales y búsqueda Exa con manejo de errores | `app/tools/`, `tests/test_tools.py`, `tests/test_exa.py` | `feat/tools-exa` |
| Mati | Panel, endpoints e integración; demo y entrega | `app/main.py`, `app/static/`, configuración raíz, README | `feat/app-demo` |

Mati coordina dependencias y cambios a `docs/CONTRATOS.md`, `.env.example` y manifiesto. Un cambio de contrato se avisa antes de implementarlo. Evitar que cuatro sesiones reescriban los mismos archivos.

## Horario de trabajo

| Hasta | Hito comprobable |
|---|---|
| 12:25 | Confirmar roles, stack, acceso API/Exa y contratos; compartir esta base en GitHub por el propietario. |
| 12:50 | Un escenario disponible, herramientas consultables, UI con fixture y agente capaz de una llamada de herramienta. |
| 13:25 | Primer flujo vertical con modelo real, evidencia local e informe visible. Integrar las ramas aunque la UI sea sencilla. |
| 14:00 | Exa en vivo, escenario benigno y manejo de errores. Cerrar nuevas funcionalidades. |
| 14:35 | Pruebas de integración, quickstart desde clon limpio y corrección de bloqueos. |
| 15:00 | Video de dos minutos grabado, descripción y evidencias de entrega completas. |
| 15:15 | Revisar enlaces, permisos y requisitos locales; enviar con margen cuando el equipo lo autorice. |
| 15:30 | Límite comunicado por Manu. |

Si un hito se retrasa, recortar animaciones, hipótesis visuales y contención opcional. Mantener investigación real, evidencia, escenario benigno e integración Exa. No sustituir una integración fallida por una simulación sin etiquetar.

## Coordinación práctica

- Tablero simple: Pendiente → En curso → En revisión → Hecho; cada tarea tiene dueño y condición de aceptación.
- Cada 25 minutos compartir: «terminé / siguiente / bloqueo / cambio de contrato». Si un bloqueo dura 10 minutos, avisar al integrador.
- Cada persona trabaja en su rama desde la misma base. PRs pequeños, con comandos probados y resultado. No hacer force push a main ni cambiar contratos en silencio.
- Integrar primero escenarios, herramientas, agente y UI en cuanto haya interfaces funcionales; no esperar a que cada parte esté perfecta.
- “Hecho” significa probado en la aplicación integrada, no solo código generado por Codex.
- Manu comparte los encargos siguientes con sus compañeros. Esta entrega incluye el módulo de consultas y Exa; cada integrante integra su parte según el contrato.

## Encargos para copiar en cada Codex

### Juan

Lee README.md y docs/CONTRATOS.md. Implementa únicamente app/agent/ y sus pruebas en feat/agent. El agente decide consultas usando las herramientas de Manu; incluye límites de pasos/tiempo, manejo de fallos e informe con IDs de evidencia válidos. Consume el contexto del escenario elegido. Prueba que puede concluir benigno o inconcluso. No cambies la API ni los datasets; comunica cualquier incompatibilidad a Mati. Entrega comandos de prueba y resultado. No publiques ni fusiones sin el flujo acordado por el equipo.

### Elías

Lee README.md y docs/CONTRATOS.md. Crea en feat/scenarios dos datasets JSON sintéticos: compromiso SSH y administración legítima. Correlaciona timestamps, host, usuario, PID, IP y conexiones. Usa IDs estables y direcciones reservadas de ejemplo. Coloca las respuestas esperadas en tests/fixtures/, separadas de los datos que ve el agente. Valida referencias, orden temporal y que el escenario benigno contiene evidencia explicativa. No implementes ataques ni cambies contratos sin coordinar con Mati.

### Manu

Lee README.md y docs/CONTRATOS.md. Implementa en feat/tools-exa las consultas locales y research_security_context con Exa. Valida argumentos y aísla consultas por escenario. Exa recibe términos públicos de técnica/mitigación, no logs crudos. Devuelve fuentes reales con URL y fragmento, y estados explícitos de error o ausencia de resultados. Añade timeout y pruebas de credencial ausente, error y resultados vacíos usando dobles de prueba. Documenta por separado si se verificó una llamada real. No cambies app/main.py ni el contrato sin coordinar con Mati.

### Mati

Lee README.md y docs/CONTRATOS.md. Implementa en feat/app-demo el backend de integración y un panel web sencillo con selector de escenario, petición de investigación, actividad real, timeline, evidencia, fuentes y reporte descargable. Integra las funciones de los compañeros según contrato. Usa polling sencillo. Etiqueta datos sintéticos y pruebas simuladas. Añade configuración de entorno sin claves y comandos de inicio comprobados. Prioriza un flujo completo antes de pulir estilos.


