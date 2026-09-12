# Integración de Manu: web → herramientas Python → datos / Exa

La web registra las mismas consultas que consume el agente Python de Juan. El servidor Next.js ejecuta `python -m app.tools.bridge` con JSON por stdin, sin shell ni comandos elegibles por el modelo. No se duplicó la implementación Exa en TypeScript para el SOC.

## Configurar en la máquina de Mati

1. Instalar dependencias del repositorio con `npm ci` y disponer de Python 3.11+.
2. Mantener `EXA_API_KEY` en `.env` raíz. Si `python` no está en PATH, definir `PYTHON_EXECUTABLE` con la ruta al ejecutable; no incluir argumentos ni comillas dentro del valor.
3. Configurar el proveedor/modelo del chat con credenciales reales del equipo. Una clave ficticia no permite conversar con el modelo.
4. Ejecutar `npm run dev:web` y abrir `http://127.0.0.1:3100`.
5. Seleccionar contenedor y probar **Consultar eventos** y **Buscar fuentes**. Estas acciones verifican las herramientas sin depender de una llamada al modelo.
6. Desde el chat pedir: «Consulta los eventos del contenedor seleccionado y busca documentación pública sobre la técnica o el fallo observado. Cita IDs de eventos y fuentes, y explica los datos que faltan».

## Conectar los datos de Elías

Los escenarios de Elías ya aparecen como `CONT-SOCA` → `scenario-a` y `CONT-SOCB` → `scenario-b`, con sus títulos neutrales y registros originales. Los dos ejemplos anteriores de Docker se conservan. Para remapear otros contenedores, configurar en `.env`:

```dotenv
SOC_SCENARIO_MAP={"CONT-8A19":"scenario-a","CONT-9B21":"scenario-b"}
```

Cada JSON mantiene el contrato documentado: id, events, processes, connections y deployments. El agente Python de Juan usa directamente ese scenario_id. Las herramientas web fijan el scenario_id en servidor desde el contenedor, y el modelo no puede elegir rutas o sobrescribirlo.

Sin archivo ni mapeo explícito se utiliza únicamente el timeline ficticio que ya muestra la UI. Se devuelven IDs estables y `provenance.source=ui_demo_timeline`, además de la limitación de procesos/conexiones/deployments no disponibles. La fecha 2026-09-12 se asigna a las horas del demo y se declara en la procedencia. No se inventan procesos ni conexiones. Un mapeo explícito ausente o un archivo inválido devuelve error en vez de esconderlo detrás del demo.

## Herramientas registradas en el chat

`inspect_container_logs` (alias de timeline), `search_logs`, `get_timeline`, `inspect_process`, `get_connections`, `get_recent_deployments` y `research_security_context`. Todas devuelven `{ok,data,error}`. El panel conserva hasta 10 resultados de la vista y muestra fuentes públicas con sus enlaces; cambiar de contenedor reinicia esa vista.

## Límites

- Exa usa el adaptador Python revisado contra build-with-exa: `/search`, auto, highlights y tres fuentes.
- Caché por sesión, contenedor y consulta durante cinco minutos. Las fallas no se guardan como éxitos.
- Dos búsquedas nuevas por contenedor y sesión cada 90 segundos; cuatro procesos simultáneos como máximo. Este presupuesto web es por ventana temporal, distinto del presupuesto por investigación que aplica Juan en Python.
- La ruta limita parámetros y tamaño de solicitud y acepta exclusivamente el origen de la aplicación en loopback. Para publicar en Internet hace falta una política deliberada de autenticación/orígenes y cuotas; no basta con cambiar el host.
- El proceso termina a los 20 segundos. No se registran stderr, claves ni texto de errores del proveedor.
- No se necesita un servidor FastAPI adicional. El despliegue debe incluir Python y permitir subprocess; un entorno que no los soporte requiere otro transporte.
- El SOC web usa `/api/soc-tools`; la ruta previa `/api/search` sigue destinada a la voz del starter y no es el camino nuevo del SOC.

## Verificación de esta entrega

- Typecheck de los tres workspaces aprobado.
- Build Next.js de producción aprobado, con una advertencia de dependencia dinámica heredada de Google Vertex/CopilotKit.
- 31 pruebas Python aprobadas, incluidas las del agente de Juan.
- 39 pruebas web, 37 de agent-core y 22 de Channels aprobadas.
- HTTP real: tres eventos del demo, tres fuentes Exa, consulta repetida desde caché y origen externo rechazado con 403.
- Navegador: panel y consulta de eventos verificados.
- Prueba del puente con los dos escenarios de Elías: IDs aislados y correlación proceso/conexión aprobadas.

Los tests tsx requirieron un preload temporal fuera del repositorio por un error `uv_os_get_passwd` de la cuenta de sandbox Windows. Los tests de agent-core/Channels se enumeraron explícitamente porque sus scripts con comillas simples ejecutan cero tests en este shell. Ningún workaround se añadió a la aplicación.

La compilación y la prueba de herramientas usaron una clave de modelo ficticia para inicializar el runtime; no se probó una conversación real ni el informe completo con el proveedor del equipo. Tampoco se probó Docker real: los datos actuales son de muestra.
