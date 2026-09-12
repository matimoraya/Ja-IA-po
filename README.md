# Ja-IA-po — agente SOC

Un asistente para un analista de seguridad que investiga actividad sospechosa, correlaciona evidencia y produce un informe verificable dentro de un panel web.

**Estado:** módulo de consultas locales y Exa implementado; 10 pruebas offline pasaron y una búsqueda real de Exa devolvió tres fuentes. El agente, la interfaz y los escenarios del equipo siguen pendientes de integración. Ver [guía de herramientas](docs/TOOLS-EXA.md).

## Objetivo del MVP

El usuario selecciona un escenario y pide «Investigá la actividad sospechosa de este servidor». El agente recibe ese contexto, elige herramientas de consulta, observa resultados y decide qué investigar después. La pantalla muestra actividad ejecutada, eventos, evidencia y conclusión; no expone razonamiento interno del modelo.

Resultado: clasificación `incident`, `benign` o `inconclusive`, severidad, timeline, evidencias identificables, explicaciones breves y recomendaciones respaldadas. No presentar porcentajes de confianza como probabilidades calibradas.

## Alcance acordado y propuesta técnica

Confirmado por Manu: equipo Matías, Elías, Juan y Manu; entrega a las 15:30; integración con Exa. El concepto SOC procede de la [conversación compartida](https://chatgpt.com/share/6aa56a98-4e34-83e9-9e1f-616c1aeccf3e).

Propuesta para el tiempo disponible: Python + FastAPI, frontend HTML/CSS/JavaScript servido por el mismo backend y un único agente con herramientas. Es una decisión inicial reemplazable antes de empezar, no una preferencia ya confirmada por todos. Un `.gitignore` Python no prueba que exista un stack previo.

- Dos escenarios sintéticos: compromiso SSH y actividad administrativa legítima que parece sospechosa.
- Consultas sobre JSON local. Nada de ejecutar ataques, comandos del host o escaneos de terceros.
- Investigación mediante modelo real con herramientas; modo de pruebas determinista identificado como tal.
- Exa para documentación pública de técnicas y mitigaciones; no como prueba de que ocurrió un ataque local.
- Informe exportable en Markdown. Datos y resultados temporales en memoria son suficientes para esta demo, claramente identificados.
- Contención simulada opcional únicamente después del MVP; sin bloquear IPs ni cuentas reales.

No incluir inicialmente Slack, móvil, autenticación multiusuario, SIEM completo, múltiples agentes ni despliegue complejo.

## Criterios de aceptación

1. Seleccionar un escenario condiciona las consultas: nunca mezcla evidencia entre escenarios.
2. El modelo puede elegir las herramientas y su siguiente paso según resultados; no se codifica una secuencia fija de investigación.
3. La investigación SSH correlaciona autenticación, proceso y conexión; cada afirmación factual apunta a eventos existentes.
4. El escenario benigno contempla la explicación administrativa y no declara un ataque solo por intentos fallidos.
5. Exa devuelve al menos una fuente real verificable durante la demo en vivo. Si falla, la UI lo informa y conserva la investigación local.
6. Hay límites de pasos, tiempo y errores, con salida `inconclusive` cuando falta evidencia.
7. La UI identifica datos sintéticos, fuentes externas y modo de prueba. No fabrica tool calls para aparentar una ejecución real.
8. Existe prueba del flujo completo, un falso positivo y un fallo de proveedor; las pruebas locales no se presentan como pruebas de integración en vivo.

## Trabajo del equipo

Ver [plan y responsables](docs/EQUIPO.md), [contratos de integración](docs/CONTRATOS.md) y [entrega](SUBMISSION.md). Cada integrante puede dar a su Codex el encargo preparado en el plan del equipo.

## Credenciales y procedencia

Se necesita verificar acceso API del proveedor del modelo y `EXA_API_KEY`. No pegar claves en chats o commits. Preparar `.env.example` sin valores privados al implementar. Créditos de ChatGPT y facturación API se administran por separado: [documentación OpenAI](https://help.openai.com/en/articles/9039756-billing-settings-in-chatgpt-vs-platform).

Heredado al clonar: `.gitignore` y su historial. La documentación de planificación se creó localmente el 12 de septiembre de 2026. Registrar separadamente la implementación real del equipo y confirmar su periodo de creación antes de la entrega.

