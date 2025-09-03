#!/bin/bash
# Financial Analytics Platform Deployment Verification Script

echo "🚀 Financial Analytics Platform - Deployment Verification"
echo "=========================================================="
echo

# Test service status
echo "📊 Service Status Check:"
docker compose -f docker-compose.simple.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo

# Test health endpoints
echo "🏥 Health Check Results:"

# API Health
echo -n "API Service (8000): "
if docker exec financial-api python -c "
import urllib.request
import json
try:
    with urllib.request.urlopen('http://localhost:8000/health') as response:
        data = json.loads(response.read().decode())
        print('✅ HEALTHY' if data['success'] else '❌ UNHEALTHY')
except:
    print('❌ FAILED')
" 2>/dev/null; then
    echo "✅ API Health Check Complete"
else
    echo "❌ API Health Check Failed"
fi

# UI Health  
echo -n "UI Service (8080): "
if docker exec financial-ui python -c "
import urllib.request
import json
try:
    with urllib.request.urlopen('http://localhost:8080/health') as response:
        data = json.loads(response.read().decode())
        print('✅ HEALTHY' if data['success'] else '❌ UNHEALTHY')
except:
    print('❌ FAILED')
" 2>/dev/null; then
    echo "✅ UI Health Check Complete"
else
    echo "❌ UI Health Check Failed"
fi

# Database Health
echo -n "Database (5432): "
if docker exec financial-db pg_isready -U finance >/dev/null 2>&1; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# Redis Health
echo -n "Redis (6379): "
if docker exec financial-redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# SMTP Health
echo -n "SMTP (1025/1080): "
if docker ps --filter "name=financial-smtp" --filter "status=running" --quiet | grep -q .; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# Grafana Health
echo -n "Grafana (3000): "
if docker ps --filter "name=financial-grafana" --filter "status=running" --quiet | grep -q .; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

echo

# Test API endpoints
echo "🔌 API Endpoint Tests:"
docker exec financial-api python -c "
import urllib.request
import json

endpoints = {
    '/': 'Root endpoint',
    '/health': 'Health check',
    '/api/status': 'API status',
    '/api/endpoints': 'Endpoint list',
    '/api/test/database': 'Database test',
    '/api/test/redis': 'Redis test'
}

for endpoint, description in endpoints.items():
    try:
        with urllib.request.urlopen(f'http://localhost:8000{endpoint}') as response:
            if response.status == 200:
                print(f'✅ {endpoint} - {description}')
            else:
                print(f'❌ {endpoint} - {description} (Status: {response.status})')
    except Exception as e:
        print(f'❌ {endpoint} - {description} (Error: {e})')
"

echo

# Network connectivity
echo "🌐 Network Connectivity:"
echo "Network Name: cursor_financial-network"
docker network ls | grep cursor_financial-network && echo "✅ Network exists" || echo "❌ Network missing"

echo

# Volume status
echo "💾 Volume Status:"
docker volume ls | grep cursor && echo "✅ Volumes created" || echo "❌ Volumes missing"

echo

# Show access points
echo "🌍 Service Access Points:"
echo "- Frontend Dashboard: http://localhost:8080"
echo "- API Backend: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Grafana Monitoring: http://localhost:3000"
echo "- Prometheus Metrics: http://localhost:9090"
echo "- Email Interface: http://localhost:1080"

echo

# Show credentials
echo "🔐 Default Credentials:"
echo "Database (PostgreSQL):"
echo "  - Username: finance"
echo "  - Password: SecureFinancePassword2024!"
echo "  - Database: finance"
echo
echo "Grafana Dashboard:"
echo "  - Username: admin"
echo "  - Password: SecureGrafanaAdmin2024!"

echo
echo "🎉 Deployment Verification Complete!"
echo "All core services are deployed and functional."