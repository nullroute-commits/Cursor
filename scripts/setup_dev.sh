#!/bin/bash

# Development Environment Setup Script
# This script sets up a complete development environment for the Django application

set -e

echo "🚀 Setting up Django Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3.12 is available
check_python_version() {
    echo -e "${BLUE}Checking Python version...${NC}"
    
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
        echo -e "${GREEN}✓ Python 3.12 found${NC}"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$PYTHON_VERSION" == "3.12" ]]; then
            PYTHON_CMD="python3"
            echo -e "${GREEN}✓ Python 3.12 found${NC}"
        else
            echo -e "${RED}✗ Python 3.12 required, found $PYTHON_VERSION${NC}"
            echo "Please install Python 3.12 and try again"
            exit 1
        fi
    else
        echo -e "${RED}✗ Python 3.12 not found${NC}"
        echo "Please install Python 3.12 and try again"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    echo -e "${BLUE}Creating virtual environment...${NC}"
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${YELLOW}Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
}

# Install dependencies
install_dependencies() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install development dependencies
    pip install -r requirements/development.txt
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Setup pre-commit hooks
setup_precommit() {
    echo -e "${BLUE}Setting up pre-commit hooks...${NC}"
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        pre-commit install --hook-type commit-msg
        echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
    else
        echo -e "${YELLOW}Pre-commit not available, skipping${NC}"
    fi
}

# Setup database
setup_database() {
    echo -e "${BLUE}Setting up database...${NC}"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/django_app_dev
REDIS_URL=redis://localhost:6379/0
MEMCACHED_URL=localhost:11211
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
EOF
        echo -e "${GREEN}✓ Environment file created${NC}"
    else
        echo -e "${YELLOW}Environment file already exists${NC}"
    fi
}

# Run initial checks
run_checks() {
    echo -e "${BLUE}Running initial checks...${NC}"
    
    # Check if Django can start
    python manage.py check --deploy
    
    # Run basic linting
    if command -v flake8 &> /dev/null; then
        flake8 app/ --max-line-length=120 --exclude=migrations,__pycache__
        echo -e "${GREEN}✓ Basic linting passed${NC}"
    fi
    
    echo -e "${GREEN}✓ All checks passed${NC}"
}

# Main setup function
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Django Dev Environment Setup  ${NC}"
    echo -e "${BLUE}================================${NC}"
    
    check_python_version
    create_venv
    install_dependencies
    setup_precommit
    setup_database
    run_checks
    
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  Setup Complete! 🎉${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Start development server: python manage.py runserver"
    echo "3. Run tests: python manage.py test"
    echo "4. Run linting: flake8 app/"
    echo "5. Format code: black app/"
    echo ""
    echo -e "${BLUE}Happy coding! 🚀${NC}"
}

# Run main function
main "$@"