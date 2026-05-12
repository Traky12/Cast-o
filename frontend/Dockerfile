FROM nginx:1.27-alpine

COPY nginx.dev.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html/

RUN find /usr/share/nginx/html -name "*.sh" -delete && \
    find /usr/share/nginx/html -name "Dockerfile" -delete && \
    chmod -R 755 /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost/index.html || exit 1

CMD ["nginx", "-g", "daemon off;"]
