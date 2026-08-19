# Build context is the repo root (see docker-compose.yml / Railway service settings)
FROM node:20-alpine

WORKDIR /app

# Install dos2unix to handle Windows line endings
RUN apk add --no-cache dos2unix

COPY src/interface-frontend/package*.json src/interface-frontend/.npmrc ./
RUN npm install

COPY src/interface-frontend/entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

COPY src/interface-frontend/ .
COPY src/customizations/tasks/ ./customizations/

EXPOSE 5173

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
