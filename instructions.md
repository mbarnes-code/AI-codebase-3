---
applyTo: '**'
---
, domain knowledge, and preferences that AI should follow.
hardware:
### **Intel NUC**
name: Jane
IP: 192.168.1.17
Current OS: Ubuntu LTS 24.04
Current CPU: i3-10110U 
Current RAM: 64GB RAM SO-DIMM DDR4 2666
Current Storage: 512GB SSD SATA 3 + 1TB NMVe 
Current Role: Service hub (databases, monitoring, APIs)
    services: Qdrant Redis N8N apache Tika postgresdb nginx XTTS MCP server Qdrant,Next.js Django fastAPI grafana/prometheus scrape4ai


### **Primary AI Server**
name: motoko
IP: 192.168.1.12
Current OS: Ubuntu LTS 24.04
Motherboard: ASUS TUF Gaming X570-Plus WiFi
Form Factor: ATX
Current CPU: AMD Ryzen 9 5900X (12C/24T, 3.7GHz base, 4.8GHz boost)
Current RAM: 128GB DDR4 3200 MHz
Current GPU: RTX 3090 (24GB VRAM)
    GPU Allocation: 20GB for AI models, 4GB buffer
Current Storage: 8TB storage NVMe Gen4 + 2TB NVMe SSD for OS
TDP Support: Up to 105W+
PCIe: 4.0 generation
Current Role: Central AI brain for all processing
Recommendation: Maximize for pure AI inference
    services: Ollama fastAPI? (Cross-device API coordination)

goals:
seperate all LLM configurations to the motoko file
finish configuring Jane as a frontend that sends request to motoko for AI services

Coding standards:
Naming Conventions:
Use clear, descriptive names for variables, functions, and files
Be consistent within the project

Code Organization
Keep functions small and focused (one task per function)
Group related code together
Use meaningful file and folder names
Separate configuration from logic

Comments and Documentation
Write comments explaining why, not what
Document complex logic and business rules
Keep comments up-to-date when code changes
Add README files for projects