FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production=false
COPY . .
ARG REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS
ENV REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS=${REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS}
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
