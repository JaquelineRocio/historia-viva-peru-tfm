# API NestJS (orquestador). Build multi-stage → imagen ligera de producción.
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/dist ./dist
# ddl.sql (fuente de verdad) para el bootstrap del esquema en producción.
COPY claude_workspace/architecture/ddl.sql ./claude_workspace/architecture/ddl.sql
COPY claude_workspace/architecture/evolution_historia_viva.sql ./claude_workspace/architecture/evolution_historia_viva.sql
EXPOSE 3000
CMD ["node", "dist/main.js"]
