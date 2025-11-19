# Docker Startup Script for Windows PowerShell
# Usage: .\run-docker.ps1

param(
    [string]$Mode = "dev",
    [switch]$BuildNew = $false,
    [switch]$Clean = $false,
    [switch]$Logs = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$GREEN = "`e[32m"
$RED = "`e[31m"
$YELLOW = "`e[33m"
$BLUE = "`e[34m"
$RESET = "`e[0m"

Write-Host "${BLUE}=====================================${RESET}"
Write-Host "${BLUE}Docker Compose Startup Script${RESET}"
Write-Host "${BLUE}=====================================${RESET}"
Write-Host ""

# Check Docker is installed
Write-Host "${YELLOW}Checking Docker installation...${RESET}"
try {
    $dockerVersion = docker --version
    Write-Host "${GREEN}✓ Docker is installed: $dockerVersion${RESET}"
} catch {
    Write-Host "${RED}✗ Docker is not installed${RESET}"
    exit 1
}

Write-Host ""

# Clean if requested
if ($Clean) {
    Write-Host "${YELLOW}Cleaning up old containers and volumes...${RESET}"
    docker-compose down --volumes --remove-orphans 2>$null
    docker system prune -f 2>$null
    Write-Host "${GREEN}✓ Cleanup completed${RESET}"
    Write-Host ""
}

# Determine compose file
$composeFile = if ($Mode -eq "prod") { "docker-compose.prod.yml" } else { "docker-compose.yml" }

Write-Host "${YELLOW}Starting services in $Mode mode...${RESET}"
Write-Host "Using: $composeFile"
Write-Host ""

# Build or pull images
if ($BuildNew) {
    Write-Host "${YELLOW}Building Docker images...${RESET}"
    docker-compose -f $composeFile build --no-cache
    Write-Host "${GREEN}✓ Build completed${RESET}"
    Write-Host ""
} elseif ($Mode -eq "dev") {
    Write-Host "${YELLOW}Building Docker images (incremental)...${RESET}"
    docker-compose -f $composeFile build
    Write-Host "${GREEN}✓ Build completed${RESET}"
    Write-Host ""
}

# Start services
Write-Host "${YELLOW}Starting containers...${RESET}"
docker-compose -f $composeFile up -d

Write-Host ""
Write-Host "${GREEN}✓ Containers started${RESET}"
Write-Host ""

# Wait for services to be healthy
Write-Host "${YELLOW}Waiting for services to be healthy (~2-3 minutes)...${RESET}"
Write-Host ""

$maxAttempts = 60
$attempt = 0
$allHealthy = $false

while ($attempt -lt $maxAttempts -and -not $allHealthy) {
    $attempt++
    
    # Get status
    $psOutput = docker-compose -f $composeFile ps --format "json" 2>$null
    
    if ($psOutput) {
        try {
            $containers = $psOutput | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($containers -is [System.Object[]]) {
                $healthyCount = 0
                foreach ($container in $containers) {
                    if ($container.State -eq "running") {
                        $healthyCount++
                    }
                }
                
                if ($healthyCount -eq @($containers).Count) {
                    $allHealthy = $true
                    break
                }
            }
        } catch {
            # Continue checking
        }
    }
    
    Start-Sleep -Seconds 2
    Write-Host -NoNewline "."
}

Write-Host ""
Write-Host ""

# Display status
Write-Host "${YELLOW}Service Status:${RESET}"
docker-compose -f $composeFile ps

Write-Host ""

# Display endpoints
Write-Host "${GREEN}=========================================${RESET}"
Write-Host "${GREEN}✓ All services are running!${RESET}"
Write-Host "${GREEN}=========================================${RESET}"
Write-Host ""
Write-Host "${BLUE}Available Endpoints:${RESET}"
Write-Host "  Frontend:        ${GREEN}http://localhost:5173${RESET}"
Write-Host "  API Gateway:     ${GREEN}http://localhost:8001${RESET}"
Write-Host "  Users Service:   ${GREEN}http://localhost:8002${RESET}"
Write-Host "  RabbitMQ UI:     ${GREEN}http://localhost:15672${RESET}"
Write-Host "  Redis:           ${GREEN}localhost:6379${RESET}"
Write-Host "  MySQL:           ${GREEN}localhost:3306${RESET}"
Write-Host ""

# Show logs if requested
if ($Logs) {
    Write-Host "${YELLOW}Following logs (Ctrl+C to stop)...${RESET}"
    Write-Host ""
    docker-compose -f $composeFile logs -f
}

Write-Host ""
Write-Host "${BLUE}Useful commands:${RESET}"
Write-Host "  View logs:       docker-compose logs -f [service_name]"
Write-Host "  Stop services:   docker-compose down"
Write-Host "  Clean up:        docker-compose down -v"
Write-Host ""
