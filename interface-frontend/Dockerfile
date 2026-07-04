# Build context is the repo root (see docker-compose.yml / Railway service settings)
FROM node:20-alpine

WORKDIR /app

# Install dos2unix to handle Windows line endings
RUN apk add --no-cache dos2unix

COPY interface-frontend/package*.json interface-frontend/.npmrc ./
RUN npm install

COPY interface-frontend/entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

COPY interface-frontend/ .
COPY customizations/tasks/ ./public/

EXPOSE 5173

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
