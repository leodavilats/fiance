# Contexto de build: a raiz do repositório (o serviço do Railway aponta para este arquivo), porque a
# imagem junta três pastas: a API, o front já compilado e os documentos de docs/.
FROM node:22-alpine AS front
WORKDIR /front
COPY fiance-trend/frontend/package.json fiance-trend/frontend/package-lock.json ./
RUN npm ci
COPY fiance-trend/frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY fiance-trend/backend/requirements.txt fiance-trend/backend/requirements.txt
RUN pip install --no-cache-dir -r fiance-trend/backend/requirements.txt
COPY fiance-trend/backend/ fiance-trend/backend/
COPY docs/ docs/
COPY --from=front /front/dist fiance-trend/frontend/dist
WORKDIR /app/fiance-trend/backend
CMD ["sh", "-c", "uvicorn api.app:criar --factory --host 0.0.0.0 --port ${PORT:-8000}"]
