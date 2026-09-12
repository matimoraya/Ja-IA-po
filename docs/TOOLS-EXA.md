# Consultas de datos y Exa — entrega de Manu

Implementado en Python 3.11+ con biblioteca estándar, sin instalar SDKs. Se usa el HTTP oficial de Exa, según `build-with-exa` v0.2.0 cargado con el comando solicitado. No hay API de modelo ni frontend en este módulo.

## Ejecutar

Desde la raíz del repositorio, con Python instalado:

```sh
python -m unittest discover -s tests -p 'test_tools.py' -v
python scripts/check_exa.py
```

El primer comando usa datos temporales y dobles de prueba; no consume créditos. El segundo hace una búsqueda real en Exa y muestra fuentes, nunca la clave.

Credenciales: `EXA_API_KEY` del entorno, después `.env`, y `API.env` como compatibilidad. `.env.example` contiene únicamente el nombre de variable. Archivos de credenciales excluidos en `.gitignore`.

## Conectar al agente de Juan

```python
from app.tools import ScenarioTools, research_security_context

# Dentro de una función async; scenario_id lo fija Mati desde el contexto del usuario.
tools = ScenarioTools(scenario_id)
logs = await tools.search_logs("SSH")
timeline = await tools.get_timeline()
process = await tools.inspect_process(host="demo-server", pid=42)
connections = await tools.get_connections(host="demo-server")
deployments = await tools.get_recent_deployments(host="demo-server")
sources = await research_security_context("SSH brute force detection and mitigation")
```

Todas las funciones retornan `{ok, data, error}` conforme al contrato. Juan registra los métodos ligados a esa instancia; no ofrece `scenario_id`, root, api_key ni transport como argumentos elegibles por el modelo. `query` local es búsqueda de subcadena sin distinguir mayúsculas; usar términos de los eventos, no esperar búsqueda semántica sobre JSON.

Elías entrega `data/scenarios/<scenario_id>/scenario.json` con `id`, `events`, `processes`, `connections`, `deployments`. Mientras no exista, la consulta retorna `SCENARIO_NOT_FOUND`. Las fechas requieren zona horaria. Los tests no agregan escenarios oficiales ni respuestas esperadas al contexto del agente.

Exa usa `/search`, `type=auto`, `contents.highlights=true` y 3 resultados como presupuesto de fuentes del MVP. No añade filtros de dominios ni fechas. URLs duplicadas se eliminan y cada fuente tiene ID estable derivado de su URL. Una fuente sin fragmento no se rellena con contenido inventado.

Juan debe limitar Exa a 2 llamadas por investigación y pasar un timeout menor si queda menos tiempo de su presupuesto global. El módulo usa 15 segundos por defecto, sin reintentos automáticos. Una cancelación detiene la espera async; la operación HTTP en su hilo termina por su timeout de socket y puede haber consumido créditos.

Las consultas a Exa deben contener términos públicos de técnicas/mitigaciones, no logs crudos ni secretos. Los fragmentos web son datos no confiables, nunca instrucciones para ejecutar acciones. El módulo no configura un LLM, no genera un informe ni contiene hosts reales.

## Validación realizada

El 12 de septiembre de 2026 pasaron 10 pruebas unittest. Una llamada real con la clave local devolvió tres fuentes. No se probó todavía la integración con el agente de Juan, la UI de Mati ni los escenarios de Elías. El kit adjunto pide npm typecheck, pero este módulo Python no contiene package.json ni TypeScript; la validación aplicable fue unittest.

