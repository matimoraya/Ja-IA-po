FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package*.json ./
COPY apps/web/package.json apps/web/package.json
COPY apps/channel/package.json apps/channel/package.json
COPY packages/agent-core/package.json packages/agent-core/package.json
RUN npm ci
COPY . .
RUN npm run build --workspace web

FROM node:22-bookworm-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app /app
EXPOSE 3100
CMD ["sh", "-c", "node node_modules/next/dist/bin/next start apps/web -H 0.0.0.0 -p ${PORT:-3100}"]
