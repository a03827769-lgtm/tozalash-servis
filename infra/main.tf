terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# --- PostgreSQL + PostGIS (Task 95) ---
resource "docker_image" "postgres" {
  name = "postgis/postgis:15-3.3"
}

resource "docker_container" "postgres" {
  image = docker_image.postgres.image_id
  name  = "tozalash_postgres"
  env = [
    "POSTGRES_USER=tozalash",
    "POSTGRES_PASSWORD=secret",
    "POSTGRES_DB=tozalash_db"
  ]
  ports {
    internal = 5432
    external = 5432
  }
  restart = "unless-stopped"
}

# --- Redis ---
resource "docker_image" "redis" {
  name = "redis:7-alpine"
}

resource "docker_container" "redis" {
  image   = docker_image.redis.image_id
  name    = "tozalash_redis"
  command = ["redis-server", "--maxmemory", "512mb", "--maxmemory-policy", "allkeys-lru"]
  ports {
    internal = 6379
    external = 6379
  }
  restart = "unless-stopped"
}

# --- Elasticsearch ---
resource "docker_image" "elasticsearch" {
  name = "elasticsearch:8.12.0"
}

resource "docker_container" "elasticsearch" {
  image = docker_image.elasticsearch.image_id
  name  = "tozalash_elasticsearch"
  env = [
    "discovery.type=single-node",
    "xpack.security.enabled=false",
    "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ]
  ports {
    internal = 9200
    external = 9200
  }
  restart = "unless-stopped"
}

# --- Kibana (ELK Stack - Task 98) ---
resource "docker_image" "kibana" {
  name = "kibana:8.12.0"
}

resource "docker_container" "kibana" {
  image = docker_image.kibana.image_id
  name  = "tozalash_kibana"
  env   = ["ELASTICSEARCH_HOSTS=http://tozalash_elasticsearch:9200"]
  ports {
    internal = 5601
    external = 5601
  }
  restart = "unless-stopped"
}

# --- Prometheus + Grafana (Task 99) ---
resource "docker_image" "prometheus" {
  name = "prom/prometheus:latest"
}

resource "docker_container" "prometheus" {
  image = docker_image.prometheus.image_id
  name  = "tozalash_prometheus"
  ports {
    internal = 9090
    external = 9090
  }
  restart = "unless-stopped"
}

resource "docker_image" "grafana" {
  name = "grafana/grafana:latest"
}

resource "docker_container" "grafana" {
  image = docker_image.grafana.image_id
  name  = "tozalash_grafana"
  ports {
    internal = 3000
    external = 3001
  }
  restart = "unless-stopped"
}
