# --- Build Angular ---
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# production build
RUN npm run build -- --configuration production


FROM nginx:1.25-alpine

COPY --from=build /app/dist/lms-frontend /usr/share/nginx/html
# Nginx that proxies /api -> gateway:8080/api
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
