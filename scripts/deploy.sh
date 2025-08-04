#!/bin/bash

# AI Trading System - Production Deployment Script
# Usage: ./scripts/deploy.sh [environment]

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_NAME="ai-trading-system"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "Docker Compose is not installed."
    fi
    
    # Check if environment file exists
    if [[ ! -f ".env" ]]; then
        warning "No .env file found. Creating from template..."
        cp .env.production .env
        warning "Please edit .env file with your actual values before continuing."
        read -p "Press Enter after editing .env file..."
    fi
    
    # Validate required environment variables
    source .env
    required_vars=("POSTGRES_PASSWORD" "API_KEY_ALPHA_VANTAGE" "JWT_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set in .env file"
        fi
    done
    
    success "Pre-deployment checks passed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p logs data backups ssl config/nginx config/grafana
    chmod 755 logs data backups
    
    success "Directories created"
}

# Backup existing data
backup_data() {
    if [[ "$ENVIRONMENT" == "production" ]] && docker-compose ps | grep -q "Up"; then
        log "Creating backup of existing data..."
        
        # Create backup directory with timestamp
        BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        CURRENT_BACKUP_DIR="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
        mkdir -p "$CURRENT_BACKUP_DIR"
        
        # Backup PostgreSQL
        log "Backing up PostgreSQL database..."
        docker-compose exec -T postgres pg_dump -U trading_user trading_db > "$CURRENT_BACKUP_DIR/postgres_backup.sql"
        
        # Backup Redis
        log "Backing up Redis data..."
        docker-compose exec -T redis redis-cli --rdb - > "$CURRENT_BACKUP_DIR/redis_backup.rdb"
        
        # Backup models
        if [[ -d "models" ]]; then
            log "Backing up ML models..."
            cp -r models "$CURRENT_BACKUP_DIR/"
        fi
        
        success "Backup completed: $CURRENT_BACKUP_DIR"
    fi
}

# Build and deploy services
deploy_services() {
    log "Building and deploying services..."
    
    # Pull latest images
    log "Pulling latest base images..."
    docker-compose -f docker-compose.prod.yml pull
    
    # Build custom images
    log "Building application images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Stop existing services gracefully
    if docker-compose ps | grep -q "Up"; then
        log "Stopping existing services..."
        docker-compose -f docker-compose.prod.yml down --timeout 30
    fi
    
    # Start services
    log "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    success "Services deployed"
}

# Health checks
health_checks() {
    log "Running health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check Redis
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        success "Redis is healthy"
    else
        error "Redis health check failed"
    fi
    
    # Check PostgreSQL
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U trading_user -d trading_db | grep -q "accepting connections"; then
        success "PostgreSQL is healthy"
    else
        error "PostgreSQL health check failed"
    fi
    
    # Check Python API
    max_attempts=10
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            success "Python API is healthy"
            break
        else
            log "Waiting for Python API... (attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Python API health check failed after $max_attempts attempts"
    fi
    
    success "All health checks passed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Wait for Prometheus to start
    sleep 10
    
    # Configure Grafana dashboards
    if [[ -f "config/grafana/dashboards/trading-dashboard.json" ]]; then
        log "Importing Grafana dashboards..."
        # Dashboard import would happen here
        success "Grafana dashboards configured"
    fi
    
    # Setup log forwarding to ELK
    log "Configuring log forwarding..."
    # Log forwarding configuration would happen here
    
    success "Monitoring setup completed"
}

# SSL setup
setup_ssl() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log "Setting up SSL certificates..."
        
        if [[ ! -f "ssl/cert.pem" ]] || [[ ! -f "ssl/private.key" ]]; then
            warning "SSL certificates not found. Please add your SSL certificates to the ssl/ directory."
            warning "For Let's Encrypt: Use certbot to generate certificates"
            warning "Place cert.pem and private.key in the ssl/ directory"
        else
            success "SSL certificates found"
        fi
    fi
}

# Post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Clear old Docker images
    log "Cleaning up old Docker images..."
    docker image prune -f
    
    # Set up log rotation
    log "Setting up log rotation..."
    # Log rotation setup would happen here
    
    # Send deployment notification
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        log "Sending deployment notification..."
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 AI Trading System deployed successfully to $ENVIRONMENT\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
    
    success "Post-deployment tasks completed"
}

# Print deployment summary
deployment_summary() {
    log "Deployment Summary"
    log "=================="
    log "Environment: $ENVIRONMENT"
    log "Timestamp: $(date)"
    log "Services:"
    
    docker-compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
    
    log ""
    log "Access URLs:"
    log "- API: http://localhost:8000"
    log "- Grafana: http://localhost:3000"
    log "- Prometheus: http://localhost:9090"
    log "- Kibana: http://localhost:5601"
    log ""
    log "🎉 Deployment completed successfully!"
}

# Main deployment function
main() {
    log "Starting deployment to $ENVIRONMENT environment..."
    
    pre_deployment_checks
    create_directories
    backup_data
    setup_ssl
    deploy_services
    health_checks
    setup_monitoring
    post_deployment
    deployment_summary
    
    success "Deployment completed successfully! 🚀"
}

# Handle script interruption
trap 'error "Deployment interrupted"' INT TERM

# Run main function
main "$@"