#!/bin/bash

# AgentMind Full Stack Startup Script
# One-command startup for complete production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
   ___                  _   __  ____           __
  / _ | ___ ____ ___  _| |_/  |/  (_)__  ___/ /
 / __ |/ _ `/ -_) _ \/ _  / /|_/ / / _ \/ _  /
/_/ |_|\_, /\__/_//_/\_,_/_/  /_/_/_//_/\_,_/
      /___/

Production Full Stack Deployment
EOF
echo -e "${NC}"

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create environment file if not exists
setup_environment() {
    log_info "Setting up environment..."

    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file not found. Creating default..."
        cat > "$ENV_FILE" << EOF
# AgentMind Production Environment Configuration

# Security
JWT_SECRET=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)
GRAFANA_PASSWORD=admin

# LLM Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_HOST=http://ollama:11434

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# API Configuration
LOG_LEVEL=info
ENABLE_METRICS=true
ENABLE_TRACING=true
RATE_LIMIT_PER_MINUTE=60
MAX_WORKERS=4

# Monitoring
PROMETHEUS_RETENTION=15d
GRAFANA_ADMIN_USER=admin
EOF
        log_success "Environment file created: $ENV_FILE"
        log_warning "Please review and update $ENV_FILE with your configuration"
    else
        log_success "Environment file found: $ENV_FILE"
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    mkdir -p traces logs data monitoring/grafana/dashboards monitoring/grafana/datasources nginx/ssl

    log_success "Directories created"
}

# Pull Docker images
pull_images() {
    log_info "Pulling Docker images..."

    docker-compose -f "$COMPOSE_FILE" pull

    log_success "Docker images pulled"
}

# Build custom images
build_images() {
    log_info "Building custom images..."

    docker-compose -f "$COMPOSE_FILE" build --parallel

    log_success "Custom images built"
}

# Start services
start_services() {
    log_info "Starting services..."

    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    log_success "Services started"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."

    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "unhealthy"; then
            attempt=$((attempt + 1))
            echo -n "."
            sleep 2
        else
            echo ""
            log_success "All services are healthy"
            return 0
        fi
    done

    echo ""
    log_warning "Some services may not be fully healthy yet"
}

# Pull Ollama model
pull_ollama_model() {
    log_info "Pulling Ollama model: $OLLAMA_MODEL..."

    docker exec agentmind-ollama ollama pull "$OLLAMA_MODEL" || {
        log_warning "Failed to pull model automatically. You can pull it manually later."
    }

    log_success "Ollama model ready"
}

# Display service URLs
display_urls() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}AgentMind is now running!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "  API Server:       ${YELLOW}http://localhost:8000${NC}"
    echo -e "  API Docs:         ${YELLOW}http://localhost:8000/docs${NC}"
    echo -e "  Chat UI:          ${YELLOW}http://localhost:5000${NC}"
    echo -e "  Dashboard:        ${YELLOW}http://localhost:3000${NC}"
    echo -e "  Prometheus:       ${YELLOW}http://localhost:9090${NC}"
    echo -e "  Grafana:          ${YELLOW}http://localhost:3001${NC}"
    echo -e "  Ollama:           ${YELLOW}http://localhost:11434${NC}"
    echo ""
    echo -e "${BLUE}Management Commands:${NC}"
    echo -e "  View logs:        ${YELLOW}docker-compose -f $COMPOSE_FILE logs -f${NC}"
    echo -e "  Stop services:    ${YELLOW}docker-compose -f $COMPOSE_FILE down${NC}"
    echo -e "  Restart services: ${YELLOW}docker-compose -f $COMPOSE_FILE restart${NC}"
    echo -e "  View status:      ${YELLOW}docker-compose -f $COMPOSE_FILE ps${NC}"
    echo ""
    echo -e "${GREEN}========================================${NC}"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
}

# Main execution
main() {
    # Parse arguments
    case "${1:-}" in
        stop)
            log_info "Stopping all services..."
            docker-compose -f "$COMPOSE_FILE" down
            log_success "All services stopped"
            exit 0
            ;;
        restart)
            log_info "Restarting all services..."
            docker-compose -f "$COMPOSE_FILE" restart
            log_success "All services restarted"
            exit 0
            ;;
        logs)
            docker-compose -f "$COMPOSE_FILE" logs -f
            exit 0
            ;;
        status)
            docker-compose -f "$COMPOSE_FILE" ps
            exit 0
            ;;
        clean)
            log_warning "This will remove all containers, volumes, and data!"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                docker-compose -f "$COMPOSE_FILE" down -v
                log_success "Cleanup complete"
            else
                log_info "Cleanup cancelled"
            fi
            exit 0
            ;;
        help|--help|-h)
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  (none)    Start all services"
            echo "  stop      Stop all services"
            echo "  restart   Restart all services"
            echo "  logs      View logs (follow mode)"
            echo "  status    Show service status"
            echo "  clean     Remove all containers and volumes"
            echo "  help      Show this help message"
            exit 0
            ;;
    esac

    # Start sequence
    check_prerequisites
    setup_environment
    create_directories
    pull_images
    build_images
    start_services
    wait_for_services
    pull_ollama_model
    display_urls
}

# Trap errors
trap cleanup ERR

# Run main
main "$@"
