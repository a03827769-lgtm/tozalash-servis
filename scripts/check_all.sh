#!/bin/bash
# Check status of all containers
echo "--- Docker Containers ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "--- Laravel API Ping ---"
curl -s http://localhost:8000/api/ping | jq || echo "API is not responding."

echo ""
echo "--- Redis Ping ---"
docker exec tozalash_redis redis-cli ping || echo "Redis is not responding."

echo ""
echo "--- MySQL Ping ---"
docker exec tozalash_mysql mysqladmin -uroot -proot_password ping || echo "MySQL is not responding."
