# Despliegue de la demo web

La aplicación necesita Node.js y Python en el mismo servicio porque Next.js llama al puente SOC mediante un subproceso controlado. El `Dockerfile` de la raíz incluye ambos runtimes.

## Variables obligatorias

```dotenv
MODEL_PROVIDER=openai
OPENAI_API_KEY=...
MODEL=gpt-5.6-sol
EXA_API_KEY=...
APP_ORIGIN=https://dominio-publico-exacto.example
```

También se puede usar OpenRouter con `MODEL_PROVIDER=openrouter`, `OPENROUTER_API_KEY` y un modelo compatible con herramientas. `APP_ORIGIN` debe ser el origen HTTPS exacto y sin barra final. No debe contener rutas.

## Construcción y ejecución

```bash
docker build -t ja-ia-po .
docker run --rm -p 3100:3100 --env-file .env ja-ia-po
```

En un proveedor compatible con contenedores, conecta el repositorio, selecciona el `Dockerfile`, agrega las variables como secretos y asigna el dominio resultante a `APP_ORIGIN`. El servidor acepta consultas SOC públicas únicamente cuando el origen del navegador coincide con ese valor.

## Comprobación antes de compartir

1. Abrir `/api/readiness` y confirmar `chatConfigured: true` y `exaConfigured: true`.
2. En la página, consultar eventos de `CONT-SOCA` y abrir una fuente de Exa.
3. Pedir al agente un análisis con IDs de evidencia y fuentes.
4. Crear una propuesta; rechazar una y aprobar otra.
5. Recargar y confirmar el límite documentado del almacenamiento usado.

Los escenarios siguen siendo sintéticos. Conectar Docker, un SIEM o telemetría de producción requiere autenticación, aislamiento por organización y un adaptador de lectura adicional; no es necesario para la demo reproducible del hackathon.
