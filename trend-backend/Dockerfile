# Contexto de build: a raiz do repositório (o serviço do Railway aponta para este arquivo), porque a
# imagem junta três pastas: a API, o front já compilado e os planos de docs/.
FROM node:22-alpine AS front
WORKDIR /front
COPY trend-frontend/package.json trend-frontend/package-lock.json ./
RUN npm ci
COPY trend-frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY trend-backend/requirements.txt trend-backend/requirements.txt
RUN pip install --no-cache-dir -r trend-backend/requirements.txt
COPY trend-backend/ trend-backend/
COPY docs/ docs/
COPY --from=front /front/dist trend-frontend/dist
WORKDIR /app/trend-backend
CMD ["sh", "-c", "uvicorn api.app:criar --factory --host 0.0.0.0 --port ${PORT:-8000}"]
