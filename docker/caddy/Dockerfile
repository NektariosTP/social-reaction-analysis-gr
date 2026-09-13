FROM node:22-alpine AS build
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# Same-origin deployment: Caddy reverse-proxies API routes on this same host,
# so the SPA should call relative paths rather than a baked-in localhost URL.
ENV VITE_API_BASE_URL=
ARG VITE_MAPTILER_KEY=
ENV VITE_MAPTILER_KEY=$VITE_MAPTILER_KEY
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY docker/caddy/Caddyfile /etc/caddy/Caddyfile
