# Deployment Guide

Complete guide for deploying the System Health Analyzer to production environments.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [AWS Deployment](#aws-deployment-terraform)
- [Manual Deployment](#manual-deployment)
- [Production Checklist](#production-checklist)

---

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Quick Deploy with Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd plant

# Create production config
cp config/config.example.yaml config/config.yaml
nano config/config.yaml  # Edit with production settings

# Set secrets
cat > .env <<EOF
ANTHROPIC_API_KEY=sk-ant-your-key
GITHUB_TOKEN=ghp_your-token
SLACK_WEBHOOK=https://hooks.slack.com/...
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/system_health
REDIS_URL=redis://redis:6379/0
EOF

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: your-registry.com/system-health-analyzer:latest
    restart: always
    ports:
      - "80:8000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env.production
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: system_health
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    shm_size: 256MB

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

### Building Custom Image

```bash
# Build
docker build -t system-health-analyzer:latest .

# Tag for registry
docker tag system-health-analyzer:latest your-registry.com/system-health-analyzer:latest

# Push
docker push your-registry.com/system-health-analyzer:latest
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.25+
- kubectl configured
- Helm 3.0+ (optional)

### Quick Deploy

```bash
# Create namespace
kubectl create namespace system-health

# Create secrets
kubectl create secret generic system-health-secrets \
  --from-literal=database-url="postgresql+asyncpg://..." \
  --from-literal=redis-url="redis://..." \
  --from-literal=anthropic-api-key="sk-ant-..." \
  --from-literal=github-token="ghp_..." \
  --from-literal=slack-webhook="https://..." \
  -n system-health

# Create ConfigMap
kubectl create configmap system-health-config \
  --from-file=config.yaml=config/config.example.yaml \
  -n system-health

# Apply manifests
kubectl apply -f deployment/kubernetes/ -n system-health

# Check status
kubectl get pods -n system-health

# Check logs
kubectl logs -f deployment/system-health-analyzer -n system-health
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment system-health-analyzer --replicas=5 -n system-health

# Auto-scaling (HPA already configured)
kubectl get hpa -n system-health
```

### Update Deployment

```bash
# Update image
kubectl set image deployment/system-health-analyzer \
  app=your-registry.com/system-health-analyzer:v2.0.0 \
  -n system-health

# Rollout status
kubectl rollout status deployment/system-health-analyzer -n system-health

# Rollback if needed
kubectl rollout undo deployment/system-health-analyzer -n system-health
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: system-health-ingress
  namespace: system-health
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: system-health-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: system-health-service
            port:
              number: 80
```

### Monitoring

```bash
# Install Prometheus & Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Configure ServiceMonitor
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: system-health-monitor
  namespace: system-health
spec:
  selector:
    matchLabels:
      app: system-health-analyzer
  endpoints:
  - port: http
    path: /metrics
EOF
```

---

## AWS Deployment (Terraform)

### Prerequisites

- AWS CLI configured
- Terraform 1.0+
- S3 bucket for state (create first)
- ECR repository for Docker images

### Initial Setup

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://system-health-terraform-state --region us-east-1

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Create ECR repository
aws ecr create-repository --repository-name system-health-analyzer --region us-east-1
```

### Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t system-health-analyzer:latest .

# Tag
docker tag system-health-analyzer:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/system-health-analyzer:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/system-health-analyzer:latest
```

### Deploy Infrastructure

```bash
cd deployment/terraform

# Create production.tfvars
cat > production.tfvars <<EOF
aws_region = "us-east-1"
environment = "production"
project_name = "system-health-analyzer"

# VPC
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# ECS
task_cpu = "2048"
task_memory = "4096"
desired_count = 3
min_capacity = 2
max_capacity = 10

# Database
db_instance_class = "db.t3.large"
db_allocated_storage = 100

# Redis
redis_node_type = "cache.t3.medium"

# ECR
ecr_repository_url = "<account-id>.dkr.ecr.us-east-1.amazonaws.com/system-health-analyzer"

# SSL Certificate
ssl_certificate_arn = "arn:aws:acm:us-east-1:..."
EOF

# Initialize Terraform
terraform init

# Plan
terraform plan -var-file=production.tfvars -out=tfplan

# Apply
terraform apply tfplan

# Get outputs
terraform output alb_dns_name
terraform output db_endpoint
```

### Store Secrets

```bash
# Database URL
aws secretsmanager create-secret \
  --name system-health-analyzer-db-url \
  --secret-string "postgresql+asyncpg://postgres:password@<rds-endpoint>:5432/system_health" \
  --region us-east-1

# API Keys
aws secretsmanager create-secret \
  --name system-health-analyzer-anthropic-key \
  --secret-string "sk-ant-your-key" \
  --region us-east-1

# Slack Webhook
aws secretsmanager create-secret \
  --name system-health-analyzer-slack-webhook \
  --secret-string "https://hooks.slack.com/..." \
  --region us-east-1
```

### Update Application

```bash
# Build new image
docker build -t system-health-analyzer:v2.0.0 .
docker tag system-health-analyzer:v2.0.0 <account-id>.dkr.ecr.us-east-1.amazonaws.com/system-health-analyzer:v2.0.0
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/system-health-analyzer:v2.0.0

# Update ECS service
aws ecs update-service \
  --cluster system-health-analyzer-cluster \
  --service system-health-analyzer-service \
  --force-new-deployment \
  --region us-east-1
```

### Monitoring

```bash
# CloudWatch Logs
aws logs tail /ecs/system-health-analyzer --follow --region us-east-1

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=system-health-analyzer-service \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

---

## Manual Deployment

For bare metal or VM deployment:

### System Requirements

- Ubuntu 20.04 LTS or newer
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ disk space
- Python 3.10+
- PostgreSQL 13+
- Redis 6+

### Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql redis-server nginx

# Create user
sudo useradd -r -s /bin/bash -d /opt/system-health system-health

# Clone application
sudo git clone <repository-url> /opt/system-health
sudo chown -R system-health:system-health /opt/system-health

# Switch to app user
sudo su - system-health

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data logs config
```

### Configure PostgreSQL

```bash
sudo -u postgres psql <<EOF
CREATE DATABASE system_health;
CREATE USER system_health WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE system_health TO system_health;
\q
EOF
```

### Configure Application

```bash
# Create config
cat > config/config.yaml <<EOF
environment: production
debug: false

database:
  url: "postgresql+asyncpg://system_health:secure_password@localhost/system_health"

api:
  host: "127.0.0.1"
  port: 8000
  workers: 4
EOF
```

### Create Systemd Service

```bash
sudo cat > /etc/systemd/system/system-health.service <<EOF
[Unit]
Description=System Health Analyzer
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=system-health
Group=system-health
WorkingDirectory=/opt/system-health
Environment="PATH=/opt/system-health/venv/bin"
ExecStart=/opt/system-health/venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable system-health
sudo systemctl start system-health
sudo systemctl status system-health
```

### Configure Nginx

```bash
sudo cat > /etc/nginx/sites-available/system-health <<EOF
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/system-health /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.example.com
```

---

## Production Checklist

### Security

- [ ] Change all default passwords
- [ ] Generate strong JWT secret
- [ ] Use HTTPS/TLS everywhere
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up API key authentication
- [ ] Configure CORS properly
- [ ] Enable audit logging
- [ ] Scan for vulnerabilities
- [ ] Set up secrets management

### Performance

- [ ] Configure connection pooling
- [ ] Enable Redis caching
- [ ] Set up CDN (if needed)
- [ ] Configure auto-scaling
- [ ] Optimize database queries
- [ ] Enable compression
- [ ] Set resource limits

### Monitoring

- [ ] Set up Prometheus metrics
- [ ] Configure Grafana dashboards
- [ ] Enable application logging
- [ ] Set up log aggregation
- [ ] Configure alerting
- [ ] Set up uptime monitoring
- [ ] Enable tracing (optional)

### Backup & Recovery

- [ ] Configure database backups
- [ ] Test restore procedures
- [ ] Set up data retention policies
- [ ] Configure disaster recovery
- [ ] Document recovery procedures

### High Availability

- [ ] Deploy multiple instances
- [ ] Configure load balancing
- [ ] Set up database replication
- [ ] Configure Redis sentinel/cluster
- [ ] Test failover procedures

### Maintenance

- [ ] Set up automated updates
- [ ] Configure log rotation
- [ ] Schedule data cleanup jobs
- [ ] Document runbooks
- [ ] Create oncall procedures

---

## Troubleshooting Deployment

### Container Won't Start

```bash
# Check logs
docker logs <container-id>

# Check configuration
docker exec <container-id> python -c "from src.config import get_config; get_config()"

# Check connectivity
docker exec <container-id> curl http://localhost:8000/health
```

### Database Connection Issues

```bash
# Test connection
docker exec <container-id> python -c "from src.database.connection import init_db; import asyncio; asyncio.run(init_db())"

# Check PostgreSQL logs
kubectl logs -f deployment/postgres -n system-health
```

### High Memory Usage

```bash
# Check metrics
kubectl top pods -n system-health

# Adjust resources
kubectl set resources deployment system-health-analyzer \
  --limits=memory=2Gi \
  --requests=memory=1Gi \
  -n system-health
```

### Slow Performance

```bash
# Check cache hit rate
curl http://localhost:8000/api/cache/stats

# Check database pool
kubectl exec -it <pod-name> -- python -c "from src.database.connection import engine; print(engine.pool.status())"

# Enable query logging
kubectl set env deployment/system-health-analyzer DB_ECHO=true -n system-health
```

---

## See Also

- [Configuration Guide](CONFIGURATION.md)
- [Security Guide](SECURITY.md)
- [Monitoring Guide](MONITORING.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
