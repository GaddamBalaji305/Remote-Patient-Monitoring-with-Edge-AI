# Frontend Dockerfile for Remote Patient Monitoring React SPA
FROM nginx:alpine

# Copy custom Nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend static files (index.html)
COPY frontend/index.html /usr/share/nginx/html/index.html

# Expose Nginx web server port
EXPOSE 3000

# Health check endpoint
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
