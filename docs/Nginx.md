# Nginx Configuration Guide

This document explains the nginx configuration for the Django Template Blog project. The configuration is designed to be
production-ready with security headers, performance optimizations, and proper service routing.

## Configuration Overview

The nginx configuration file is located at `infra/conf/nginx/default.conf` and serves as a reverse proxy for:

- **Backend API** (Django application)
- **MinIO Storage** (Object storage service)
- **Frontend** (Optional, currently commented out)

## Upstream Configuration

### Backend Upstream

```nginx
upstream backend_upstream {
    server backend:8000;
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}
```

**Parameters explained:**

- `server backend:8000` - Points to Django container on port 8000
- `keepalive 32` - Maintains 32 persistent connections to reduce TCP overhead
- `keepalive_requests 100` - Maximum 100 requests per connection before closing
- `keepalive_timeout 60s` - Keep idle connections alive for 60 seconds

### MinIO Upstream

```nginx
upstream minio_upstream {
    server minio:9002;
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}
```

**Purpose:** Handles file storage requests to MinIO object storage service on port 9002.

## Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Security benefits:**

- `X-Frame-Options` - Prevents clickjacking attacks by disallowing iframe embedding from other domains
- `X-Content-Type-Options` - Prevents MIME-type sniffing attacks
- `X-XSS-Protection` - Enables browser's XSS filter (legacy browsers)
- `Referrer-Policy` - Controls referrer information leakage

## Location Blocks

### Dynamic MinIO Storage

```nginx
location ~ ^/storage/(?<bucket>[^/]+)(/.*)?$ {
    proxy_pass http://minio_upstream/$bucket$2;
    # ... CORS and proxy settings
}
```

**Features:**

- **Dynamic bucket routing** - Supports multiple buckets: `/storage/images/`, `/storage/documents/`
- **CORS support** - Configured for web applications with credentials
- **Regex explanation:**
    - `^/storage/` - Matches URLs starting with "/storage/"
    - `(?<bucket>[^/]+)` - Captures bucket name (any characters except "/")
    - `(/.*)?$` - Optionally captures the rest of the path

**Examples:**

- `/storage/images/photo.jpg` → MinIO: `/images/photo.jpg`
- `/storage/docs/file.pdf` → MinIO: `/docs/file.pdf`

### Backend API Routes

```nginx
location ~ ^/(api|admin)/ {
    proxy_pass http://backend_upstream;
    # ... proxy configuration
}
```

**Routing:**

- `/api/` - Django REST API endpoints
- `/admin/` - Django admin interface

**Performance settings:**

- `proxy_buffering off` - Disables buffering for real-time responses
- `proxy_buffer_size 64k` - Large buffer for headers (supports big JSON responses)
- `proxy_buffers 8 64k` - 8 buffers × 64k = 512k total buffering
- `proxy_busy_buffers_size 128k` - Maximum data sent to client simultaneously

### Health Check

```nginx
location /health {
    access_log off;
    add_header Content-Type text/plain always;
    add_header Cache-Control "no-cache, no-store, must-revalidate" always;
    return 200 'healthy\n';
}
```

**Purpose:** Provides a simple endpoint for load balancers and monitoring systems to check if nginx is responding.

### Nginx Status Monitoring

```nginx
location /nginx-status {
    stub_status on;
    access_log off;

    allow 127.0.0.1;
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;
}
```

**Purpose:** Exposes nginx statistics for monitoring. Access is restricted to private networks only for security.

## Performance Optimizations

### Connection Pooling

- **Keepalive connections** reduce TCP handshake overhead
- **Connection reuse** improves response times by ~100ms per request
- **Optimized timeouts** balance resource usage and performance

### Buffer Sizing

- **Large buffers (64k)** handle big API responses efficiently
- **Multiple buffers (8×64k)** allow concurrent processing
- **Strategic buffering** reduces disk I/O and improves throughput

### Timeout Configuration

```nginx
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
```

**Reasoning:**

- **300 seconds** allows for long-running operations (file uploads, heavy queries)
- **Unified timeouts** across all services for consistency
- **Balance** between user experience and resource utilization

## CORS Configuration

```nginx
add_header 'Access-Control-Allow-Origin' '$http_origin' always;
add_header 'Access-Control-Allow-Credentials' 'true' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
```

**Features:**

- **Dynamic origin** - Only allows the requesting domain (more secure than `*`)
- **Credentials support** - Allows cookies and authorization headers
- **Full HTTP methods** - Supports all RESTful operations
- **Preflight handling** - Properly handles OPTIONS requests

## Frontend Configuration (Optional)

The frontend location block is commented out but ready to use:

```nginx
# location / {
#     proxy_pass http://frontend_upstream;
#     # ... configuration for frontend app
# }
```

**To enable:**

1. Uncomment the `frontend_upstream` block
2. Uncomment the `location /` block
3. Update the frontend service name and port as needed

## Common Troubleshooting

### Configuration Updates

When updating nginx configuration in Docker Swarm:

1. Update the configuration file
2. Redeploy the stack: `docker stack deploy -c stack.yml myapp`
3. Restart nginx container through Portainer or: `docker service update --force myapp_nginx`

### Testing Configuration

```bash
# Test nginx configuration syntax
docker exec nginx_container nginx -t

# Reload configuration without downtime
docker exec nginx_container nginx -s reload
```

### Common Issues

- **502 Bad Gateway** - Backend service not responding, check container connectivity
- **413 Request Entity Too Large** - Increase `client_max_body_size` (currently 100M)
- **CORS errors** - Verify origin headers and CORS configuration
- **Timeout errors** - Adjust proxy timeout values based on application needs

## Best Practices

1. **Security First** - Always use security headers and restrict monitoring endpoints
2. **Performance Tuning** - Adjust buffer sizes based on your application's response patterns
3. **Monitoring** - Use `/health` and `/nginx-status` endpoints for observability
4. **Documentation** - Keep this documentation updated when changing configuration
5. **Testing** - Always test configuration changes in staging before production

## File Location

- **Configuration file:** `infra/conf/nginx/default.conf`
- **Docker volume mount:** This file is mounted into the nginx container
- **Backup:** Always backup configuration before making changes
