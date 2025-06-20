AI Second Brain Platform Development Instructions
Project Context
Primary Goal: AI-powered ADHD/autism executive function support with cybersecurity research capabilities
Architecture: Multi-device conversation-centric system with intelligent code analysis
Development Phase: Currently implementing 22-day installation plan (see PROJECT_SPECIFICATION.md)
Target User: Solo developer with ADHD needing executive function scaffolding and cybersecurity tool consolidation
Hardware Architecture
Intel NUC "Jane" (Service Hub - Resource Constrained)

IP: 192.168.1.17
OS: Ubuntu LTS 24.04
CPU: i3-10110U (2 cores, 4 threads) - BOTTLENECK
RAM: 64GB DDR4 2666 (abundant)
Storage: 512GB SSD + 1TB NVMe
Role: API gateway, databases, ADHD support, code analysis orchestration
Resource Strategy: Smart scheduling between ADHD support (always priority) and code analysis (on-demand)

Primary AI Server "Motoko" (The Brain - High Performance)

IP: 192.168.1.12
OS: Ubuntu LTS 24.04
CPU: AMD Ryzen 9 5900X (12C/24T)
RAM: 128GB DDR4 3200
GPU: RTX 3090 (20GB for AI models, 4GB buffer)
Storage: 8TB NVMe Gen4 + 2TB NVMe SSD
Role: AI inference, heavy computation, context management

Synology NAS (Memory & Learning)

Storage: ~40TB usable
Role: Knowledge storage, automated learning, file management

Current Development Goals
Immediate (Phase 1-3)

Separate all LLM configurations to motoko - Move AI workloads off Jane
Configure Jane as frontend - API gateway that sends AI requests to motoko
Implement ADHD support stack - Daily driver functionality (priority #1)
Establish secure device communication - VPN and authentication

Long-term (Phase 4-10)

MCP server implementation - Code analysis and conversion capabilities
Cybersecurity tool integration - Unified reconnaissance and analysis platform
Learning system deployment - Automated knowledge building and pattern recognition

Development Principles
Architecture Patterns

Container-first: All services in Docker with compose orchestration
API-driven: RESTful APIs with OpenAPI specs for all inter-service communication
Resource-aware: Intelligent scheduling based on Jane's CPU constraints
Security-first: VPN-only communication, certificate auth, secrets management
Modular design: Independent services that can be scaled/replaced individually

Performance Requirements

ADHD support: Sub-second response times, always available (uses <20% CPU on Jane)
AI inference: Offload to motoko for heavy processing
Code analysis: On-demand containers that start/stop based on need
Background tasks: Scheduled during off-peak hours

Service Communication
User → Jane (nginx) → Authentication → Service Router → Target Service
                                    ↓
AI Requests → Jane (API) → motoko (Ollama/FastAPI) → Response
Coding Standards
Naming Conventions

Variables: snake_case for Python, camelCase for JavaScript/TypeScript
Environment vars: UPPERCASE_WITH_UNDERSCORES
Be consistent: Follow existing patterns within each device folder
Be descriptive: Clear, meaningful names over abbreviations

Code Organization

Device-based structure: Organize by target hardware (jane-nuc/, motoko-ai/, shared/)
Logical grouping: Keep related services and configs together
Clear separation: Configs separate from application logic
Consistent patterns: Follow existing project structure rather than forcing rigid templates

Container Standards

Base images: Use official, minimal images (python:3.11-slim, node:18-alpine)
Multi-stage builds: Separate build and runtime stages
Health checks: All containers must have health endpoints
Resource limits: Set CPU/memory limits based on Jane's constraints
Security: Non-root users, readonly filesystems where possible

API Design

RESTful endpoints with consistent HTTP methods
OpenAPI/Swagger documentation for all APIs
Structured error responses with consistent format
Rate limiting to protect Jane's limited CPU
Authentication required for all endpoints except health checks

Configuration Management

Environment-specific configs via .env files
Secrets via Vault - never hardcode credentials
Feature flags for gradual rollouts
Centralized logging with structured JSON format

Development Workflow

Create feature branch from main
Implement with tests - TDD approach preferred
Docker build and test locally
Update documentation if APIs change
Test integration with dependent services
Deploy to staging (if available) before production

GitHub Copilot Agent Guidelines
Context Setting
Always reference these key contexts when generating code:

Resource constraints: Jane has limited CPU (i3-10110U)
User needs: ADHD support is priority #1, must be fast and reliable
Architecture: Multi-device system with secure communication
Current phase: Check PROJECT_SPECIFICATION.md for installation progress

Code Generation Preferences

Work with existing structure: Adapt to the actual project organization
Generate complete, working examples rather than pseudocode
Include error handling and logging for all functions
Consider deployment target: Jane-specific code should respect CPU constraints
Provide practical solutions: Focus on working implementations over theoretical perfection
Include necessary configs: Docker, environment, and deployment configurations
Security by default: Input validation, proper authentication, secure practices

Service Creation Guidelines
When creating new services, prioritize:

Containerization: Docker-ready with appropriate resource limits
Health monitoring: Health check endpoints for system monitoring
Configuration: Environment-based config management
Logging: Structured logging for debugging and monitoring
Error handling: Robust error responses and recovery
Security: Authentication integration where appropriate
Documentation: Clear setup and usage instructions

Security Considerations

No hardcoded secrets - use environment variables or Vault
Input validation for all API endpoints
Rate limiting for resource protection
HTTPS only with proper certificate management
Principle of least privilege for service permissions

Testing Strategy

Unit tests: All business logic functions
Integration tests: Service-to-service communication
Health checks: Automated monitoring endpoints
Load testing: Ensure Jane can handle expected traffic
Security testing: Basic vulnerability scans

Documentation Requirements

README.md: Setup, configuration, usage examples
API docs: OpenAPI/Swagger for all endpoints
Architecture diagrams: Service interactions and data flow
Troubleshooting guides: Common issues and solutions
Configuration reference: All environment variables and settings

Monitoring and Observability

Structured logging: JSON format with consistent fields
Metrics collection: Prometheus-compatible metrics
Health monitoring: Grafana dashboards for system health
Alerting: Critical issues and resource exhaustion
Performance tracking: Response times and resource usage

Remember: The primary user has ADHD and needs systems that work reliably without complexity. Prioritize simplicity, clear feedback, and robust error handling over clever optimizations.