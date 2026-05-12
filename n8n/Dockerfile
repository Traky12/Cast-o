# Opcional: imagen n8n con workflows precargados en el volumen.
# Por defecto se usa la imagen oficial en docker-compose.
FROM n8nio/n8n:1.0
USER node
COPY --chown=node:node workflows /home/node/.n8n/workflows
WORKDIR /home/node/.n8n
