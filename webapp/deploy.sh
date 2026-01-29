#!/bin/bash

# Hellas Fraud Game Webapp Deployment Script
# Usage: ./deploy.sh [target]
# Targets: build, preview, netlify, vercel, gh-pages, s3

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DIST_DIR="dist"
APP_NAME="hellas-fraud-game"

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          Hellas Fraud Game - Deployment Script             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check if we're in the webapp directory
check_directory() {
    if [ ! -f "package.json" ]; then
        print_error "Error: package.json not found. Run this script from the webapp directory."
        exit 1
    fi
}

# Install dependencies if needed
install_deps() {
    if [ ! -d "node_modules" ]; then
        print_step "Installing dependencies..."
        npm install
    fi
}

# Build the application
build_app() {
    print_step "Building production bundle..."
    npm run build

    if [ -d "$DIST_DIR" ]; then
        print_success "Build completed successfully!"
        echo "  Output: $(pwd)/$DIST_DIR"
        echo "  Size: $(du -sh $DIST_DIR | cut -f1)"
    else
        print_error "Build failed - dist directory not found"
        exit 1
    fi
}

# Preview the build locally
preview_build() {
    print_step "Starting preview server..."
    npm run preview
}

# Deploy to Netlify
deploy_netlify() {
    print_step "Deploying to Netlify..."

    # Check if netlify-cli is installed
    if ! command -v netlify &> /dev/null; then
        print_warning "Netlify CLI not found. Installing..."
        npm install -g netlify-cli
    fi

    # Deploy
    if [ "$1" == "prod" ]; then
        netlify deploy --prod --dir=$DIST_DIR
    else
        netlify deploy --dir=$DIST_DIR
        print_warning "This was a draft deploy. Use './deploy.sh netlify prod' for production."
    fi
}

# Deploy to Vercel
deploy_vercel() {
    print_step "Deploying to Vercel..."

    # Check if vercel is installed
    if ! command -v vercel &> /dev/null; then
        print_warning "Vercel CLI not found. Installing..."
        npm install -g vercel
    fi

    # Deploy
    if [ "$1" == "prod" ]; then
        vercel --prod
    else
        vercel
        print_warning "This was a preview deploy. Use './deploy.sh vercel prod' for production."
    fi
}

# Deploy to GitHub Pages
deploy_gh_pages() {
    print_step "Deploying to GitHub Pages..."

    # Check if gh-pages is installed
    if ! npm list gh-pages &> /dev/null; then
        print_warning "gh-pages not found. Installing..."
        npm install --save-dev gh-pages
    fi

    # Add base path for GitHub Pages if needed
    REPO_NAME=$(basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || echo "")
    if [ -n "$REPO_NAME" ]; then
        print_warning "Note: You may need to set 'base' in vite.config.ts to '/$REPO_NAME/'"
    fi

    # Deploy using gh-pages
    npx gh-pages -d $DIST_DIR

    print_success "Deployed to GitHub Pages!"
}

# Deploy to AWS S3
deploy_s3() {
    print_step "Deploying to AWS S3..."

    # Check if aws cli is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first:"
        echo "  https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi

    # Check for bucket name
    if [ -z "$1" ]; then
        print_error "S3 bucket name required. Usage: ./deploy.sh s3 <bucket-name>"
        exit 1
    fi

    BUCKET_NAME=$1

    # Sync to S3
    aws s3 sync $DIST_DIR s3://$BUCKET_NAME --delete

    print_success "Deployed to S3 bucket: $BUCKET_NAME"
    echo "  URL: http://$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
}

# Deploy to a custom server via rsync
deploy_rsync() {
    print_step "Deploying via rsync..."

    if [ -z "$1" ]; then
        print_error "Server destination required. Usage: ./deploy.sh rsync user@server:/path"
        exit 1
    fi

    DESTINATION=$1

    rsync -avz --delete $DIST_DIR/ $DESTINATION

    print_success "Deployed to $DESTINATION"
}

# Generate a Docker deployment
generate_docker() {
    print_step "Generating Docker configuration..."

    # Create Dockerfile
    cat > Dockerfile << 'EOF'
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

    # Create nginx config
    cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

    # Create docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  webapp:
    build: .
    ports:
      - "8080:80"
    restart: unless-stopped
EOF

    print_success "Docker configuration generated!"
    echo "  Files created: Dockerfile, nginx.conf, docker-compose.yml"
    echo ""
    echo "  To build and run:"
    echo "    docker-compose up -d"
    echo ""
    echo "  Or manually:"
    echo "    docker build -t $APP_NAME ."
    echo "    docker run -p 8080:80 $APP_NAME"
}

# Show usage
show_usage() {
    echo "Usage: ./deploy.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  build              Build the production bundle"
    echo "  preview            Preview the production build locally"
    echo "  netlify [prod]     Deploy to Netlify (add 'prod' for production)"
    echo "  vercel [prod]      Deploy to Vercel (add 'prod' for production)"
    echo "  gh-pages           Deploy to GitHub Pages"
    echo "  s3 <bucket>        Deploy to AWS S3 bucket"
    echo "  rsync <dest>       Deploy via rsync to server"
    echo "  docker             Generate Docker deployment files"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh build"
    echo "  ./deploy.sh netlify prod"
    echo "  ./deploy.sh s3 my-bucket-name"
    echo "  ./deploy.sh rsync user@server.com:/var/www/hellas"
}

# Main
print_header
check_directory

case "$1" in
    build)
        install_deps
        build_app
        ;;
    preview)
        install_deps
        build_app
        preview_build
        ;;
    netlify)
        install_deps
        build_app
        deploy_netlify $2
        ;;
    vercel)
        install_deps
        build_app
        deploy_vercel $2
        ;;
    gh-pages)
        install_deps
        build_app
        deploy_gh_pages
        ;;
    s3)
        install_deps
        build_app
        deploy_s3 $2
        ;;
    rsync)
        install_deps
        build_app
        deploy_rsync $2
        ;;
    docker)
        generate_docker
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        if [ -z "$1" ]; then
            # Default: just build
            install_deps
            build_app
            echo ""
            echo "Run './deploy.sh help' to see deployment options."
        else
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
        fi
        ;;
esac
