# CASTÚO-SYSTEM™ | Imagen TRL11 — Build inmutable para CI/CD (misma base que compose)
# Build: docker buildx build -t castuo/bookstack:trl11.<sha> .
ARG BOOKSTACK_IMAGE=lscr.io/linuxserver/bookstack:latest
FROM ${BOOKSTACK_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/castuo/castuo-system"
LABEL castuo.trl="11"
LABEL castuo.sdlc="secure"
