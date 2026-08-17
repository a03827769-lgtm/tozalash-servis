#!/bin/bash
# Task 40: Backup Script for PostgreSQL and Redis
# This script is meant to be run via a Cron job (e.g., daily at 2 AM)

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="tozalash_postgres"
REDIS_CONTAINER="tozalash_redis"
DB_USER="tozalash_user"
DB_NAME="tozalash_db"

mkdir -p $BACKUP_DIR

echo "Starting backups at $TIMESTAMP..."

# 1. PostgreSQL Backup (pg_dump)
PG_BACKUP_FILE="$BACKUP_DIR/pg_backup_$TIMESTAMP.sql.gz"
echo "Backing up PostgreSQL to $PG_BACKUP_FILE..."
docker exec -t $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME | gzip > $PG_BACKUP_FILE

# 2. Redis Backup (SAVE and copy dump.rdb)
REDIS_BACKUP_FILE="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"
echo "Triggering Redis SAVE..."
docker exec -t $REDIS_CONTAINER redis-cli SAVE
echo "Copying Redis dump to $REDIS_BACKUP_FILE..."
# Assuming redis stores dump in /data/dump.rdb
docker cp $REDIS_CONTAINER:/data/dump.rdb $REDIS_BACKUP_FILE

echo "Backups completed successfully!"
