#!/bin/bash
# Tozalash Servis Database Backup Script
# Place this in a cron job: 0 2 * * * /path/to/scripts/backup_db.sh

BACKUP_DIR="../backups"
TIMESTAMP=$(date +"%F")
BACKUP_FILE="$BACKUP_DIR/tozalash_db_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

# Source environment variables if .env exists
if [ -f ../.env ]; then
  export $(cat ../.env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "Starting database backup to $BACKUP_FILE..."

# Docker exec to dump the database
docker exec tozalash_mysql sh -c 'exec mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo "Backup completed successfully."
  # Remove backups older than 30 days
  find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +30 -exec rm {} \;
else
  echo "Error creating backup!"
  exit 1
fi
