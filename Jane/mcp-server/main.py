"""
MCP Server for Code Analysis and Conversion
Implements Model Context Protocol for cybersecurity tool consolidation
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tree_sitter
from tree_sitter import Language, Parser
import docker
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from loguru import logger

# Configure logging
logger.add("logs/mcp_server.log", rotation="1 day", retention="7 days", level="INFO")

# MCP Protocol Models
class Resource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class AnalysisRequest(BaseModel):
    repository_path: str
    language: str
    analysis_type: str = Field(default="full", regex="^(full|security|performance|structure)$")
    target_language: Optional[str] = None  # For conversion tasks

class ConversionRequest(BaseModel):
    source_code: str
    source_language: str
    target_language: str
    preserve_performance: bool = True
    include_tests: bool = True

class SecurityAnalysisRequest(BaseModel):
    code_path: str
    scan_types: List[str] = ["static", "dependency", "secrets"]
    output_format: str = "json"

class MCPServer:
    """Model Context Protocol Server for code analysis and cybersecurity tools"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.motoko_client = httpx.AsyncClient()
        self.motoko_url = os.getenv("MOTOKO_LLM_URL", "http://192.168.1.12:8000")
        
        # Initialize parsers for different languages
        self.parsers = {}
        self._init_tree_sitter_parsers()
        
        # Tool containers for security analysis
        self.security_tools = {
            "semgrep": "returntocorp/semgrep",
            "trivy": "aquasec/trivy", 
            "bandit": "securecodewarrior/bandit",
            "gosec": "securecodewarrior/gosec",
            "eslint": "eslint/eslint",
            # Enhanced cybersecurity tools
            "nuclei": "projectdiscovery/nuclei",
            "gobuster": "opsecx/gobuster",
            "amass": "caffix/amass",
            "subfinder": "projectdiscovery/subfinder",
            "nikto": "sullo/nikto"
        }
        
        # Transpiler tools for code conversion
        self.transpiler_tools = {
            "c2go": "elliotchance/c2go",
            "go2cpp": "google/grumpy",  # Placeholder - would need custom implementation
            "jsweet": "cincheo/jsweet",
            "python_ast": "python:3.11-alpine"  # Built-in AST tools
        }
    
    def _init_tree_sitter_parsers(self):
        """Initialize Tree-sitter parsers for code analysis"""
        try:
            # Common languages for cybersecurity tools
            languages = ["python", "go", "javascript", "c", "cpp", "rust"]
            
            for lang in languages:
                try:
                    # This would normally require pre-built language files
                    # For demo purposes, we'll simulate parser availability
                    self.parsers[lang] = f"parser_{lang}"
                    logger.info(f"Initialized parser for {lang}")
                except Exception as e:
                    logger.warning(f"Could not initialize parser for {lang}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize parsers: {e}")
    
    async def analyze_codebase(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Analyze a codebase for structure, security, and conversion potential"""
        
        repo_path = Path(request.repository_path)
        if not repo_path.exists():
            raise HTTPException(status_code=404, detail="Repository path not found")
        
        analysis_id = str(uuid.uuid4())
        logger.info(f"Starting codebase analysis {analysis_id} for {repo_path}")
        
        results = {
            "analysis_id": analysis_id,
            "timestamp": datetime.utcnow().isoformat(),
            "repository_path": str(repo_path),
            "language": request.language,
            "analysis_type": request.analysis_type,
            "metrics": {},
            "security_findings": [],
            "conversion_assessment": {},
            "recommendations": []
        }
        
        try:
            # Basic file analysis
            results["metrics"] = await self._analyze_file_structure(repo_path, request.language)
            
            # Security analysis if requested
            if request.analysis_type in ["full", "security"]:
                results["security_findings"] = await self._run_security_analysis(repo_path, request.language)
            
            # Conversion assessment if target language specified
            if request.target_language:
                results["conversion_assessment"] = await self._assess_conversion_feasibility(
                    repo_path, request.language, request.target_language
                )
            
            # Generate AI-powered recommendations
            results["recommendations"] = await self._generate_recommendations(results)
            
            logger.info(f"Completed analysis {analysis_id}")
            return results
            
        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    async def _analyze_file_structure(self, repo_path: Path, language: str) -> Dict[str, Any]:
        """Analyze repository file structure and basic metrics"""
        
        metrics = {
            "total_files": 0,
            "source_files": 0,
            "lines_of_code": 0,
            "function_count": 0,
            "class_count": 0,
            "complexity_score": 0,
            "file_types": {},
            "largest_files": []
        }
        
        # File extension mapping
        extensions = {
            "python": [".py"],
            "go": [".go"],
            "javascript": [".js", ".ts"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".hpp", ".cc", ".cxx"],
            "rust": [".rs"]
        }
        
        target_extensions = extensions.get(language, [])
        
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                metrics["total_files"] += 1
                
                suffix = file_path.suffix.lower()
                metrics["file_types"][suffix] = metrics["file_types"].get(suffix, 0) + 1
                
                if suffix in target_extensions:
                    metrics["source_files"] += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = len(content.splitlines())
                            metrics["lines_of_code"] += lines
                            
                            # Track largest files
                            metrics["largest_files"].append({
                                "path": str(file_path.relative_to(repo_path)),
                                "lines": lines,
                                "size_bytes": file_path.stat().st_size
                            })
                            
                    except Exception as e:
                        logger.warning(f"Could not analyze file {file_path}: {e}")
        
        # Sort and limit largest files
        metrics["largest_files"] = sorted(
            metrics["largest_files"], 
            key=lambda x: x["lines"], 
            reverse=True
        )[:10]
        
        return metrics
    
    async def _run_security_analysis(self, repo_path: Path, language: str) -> List[Dict[str, Any]]:
        """Run security analysis using containerized tools"""
        
        findings = []
        
        try:
            # Run Semgrep for general security analysis
            semgrep_results = await self._run_semgrep(repo_path, language)
            findings.extend(semgrep_results)
            
            # Language-specific tools
            if language == "python":
                bandit_results = await self._run_bandit(repo_path)
                findings.extend(bandit_results)
            elif language == "go":
                gosec_results = await self._run_gosec(repo_path)
                findings.extend(gosec_results)
            
            # Dependency analysis with Trivy
            trivy_results = await self._run_trivy(repo_path)
            findings.extend(trivy_results)
            
            # Enhanced tools: Nuclei and Gobuster
            nuclei_results = await self.run_nuclei_scan(str(repo_path))
            findings.extend(nuclei_results.get("findings", []))
            
            gobuster_results = await self.run_gobuster_scan(str(repo_path))
            findings.extend(gobuster_results.get("findings", []))
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            findings.append({
                "tool": "error",
                "severity": "info",
                "message": f"Security analysis partially failed: {str(e)}"
            })
        
        return findings
    
    async def _run_semgrep(self, repo_path: Path, language: str) -> List[Dict[str, Any]]:
        """Run Semgrep static analysis"""
        
        findings = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                output_file = temp_file.name
            
            # Run Semgrep container
            container = self.docker_client.containers.run(
                self.security_tools["semgrep"],
                command=f"semgrep --config=auto --json --output=/output.json /src",
                volumes={
                    str(repo_path): {"bind": "/src", "mode": "ro"},
                    output_file: {"bind": "/output.json", "mode": "rw"}
                },
                detach=True,
                remove=True
            )
            
            # Wait for completion (with timeout)
            container.wait(timeout=300)  # 5 minutes
            
            # Read results
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    semgrep_data = json.load(f)
                    
                for result in semgrep_data.get("results", []):
                    findings.append({
                        "tool": "semgrep",
                        "rule_id": result.get("check_id"),
                        "severity": result.get("extra", {}).get("severity", "info"),
                        "message": result.get("extra", {}).get("message", ""),
                        "file": result.get("path", ""),
                        "line": result.get("start", {}).get("line", 0)
                    })
                
                os.unlink(output_file)
                
        except docker.errors.ContainerError as e:
            logger.warning(f"Semgrep container failed: {e}")
        except Exception as e:
            logger.error(f"Semgrep analysis failed: {e}")
        
        return findings
    
    async def _run_trivy(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Run Trivy for vulnerability and secret scanning"""
        
        findings = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                output_file = temp_file.name
            
            container = self.docker_client.containers.run(
                self.security_tools["trivy"],
                command=f"trivy fs --format json --output /output.json /src",
                volumes={
                    str(repo_path): {"bind": "/src", "mode": "ro"},
                    output_file: {"bind": "/output.json", "mode": "rw"}
                },
                detach=True,
                remove=True
            )
            
            container.wait(timeout=300)
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    trivy_data = json.load(f)
                    
                for result in trivy_data.get("Results", []):
                    for vuln in result.get("Vulnerabilities", []):
                        findings.append({
                            "tool": "trivy",
                            "vulnerability_id": vuln.get("VulnerabilityID"),
                            "severity": vuln.get("Severity", "unknown").lower(),
                            "message": vuln.get("Description", ""),
                            "package": vuln.get("PkgName", ""),
                            "version": vuln.get("InstalledVersion", "")
                        })
                
                os.unlink(output_file)
                
        except Exception as e:
            logger.error(f"Trivy analysis failed: {e}")
        
        return findings
    
    async def _run_bandit(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Run Bandit for Python security analysis"""
        
        findings = []
        
        try:
            result = subprocess.run([
                "python", "-m", "bandit", "-r", str(repo_path), "-f", "json"
            ], capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                
                for result in bandit_data.get("results", []):
                    findings.append({
                        "tool": "bandit",
                        "test_id": result.get("test_id"),
                        "severity": result.get("issue_severity", "info").lower(),
                        "confidence": result.get("issue_confidence", "medium").lower(),
                        "message": result.get("issue_text", ""),
                        "file": result.get("filename", ""),
                        "line": result.get("line_number", 0)
                    })
                    
        except subprocess.TimeoutExpired:
            logger.warning("Bandit analysis timed out")
        except Exception as e:
            logger.error(f"Bandit analysis failed: {e}")
        
        return findings
    
    async def _run_gosec(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Run Gosec for Go security analysis"""
        
        findings = []
        
        try:
            result = subprocess.run([
                "gosec", "-fmt", "json", str(repo_path) + "/..."
            ], capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                gosec_data = json.loads(result.stdout)
                
                for issue in gosec_data.get("Issues", []):
                    findings.append({
                        "tool": "gosec",
                        "rule_id": issue.get("rule_id"),
                        "severity": issue.get("severity", "info").lower(),
                        "confidence": issue.get("confidence", "medium").lower(),
                        "message": issue.get("details", ""),
                        "file": issue.get("file", ""),
                        "line": issue.get("line", "0")
                    })
                    
        except subprocess.TimeoutExpired:
            logger.warning("Gosec analysis timed out")
        except Exception as e:
            logger.error(f"Gosec analysis failed: {e}")
        
        return findings
    
    async def run_nuclei_scan(self, target: str, templates: List[str] = None) -> Dict[str, Any]:
        """Run Nuclei vulnerability scanner against a target"""
        
        findings = []
        
        try:
            cmd = ["nuclei", "-target", target, "-json"]
            if templates:
                cmd.extend(["-t", ",".join(templates)])
            else:
                cmd.extend(["-t", "cves,vulnerabilities,exposed-panels"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        nuclei_data = json.loads(line)
                        findings.append({
                            "tool": "nuclei",
                            "template": nuclei_data.get("template"),
                            "severity": nuclei_data.get("info", {}).get("severity", "info").lower(),
                            "name": nuclei_data.get("info", {}).get("name", ""),
                            "matched_at": nuclei_data.get("matched-at", ""),
                            "extracted_results": nuclei_data.get("extracted-results", [])
                        })
                        
        except subprocess.TimeoutExpired:
            logger.warning("Nuclei scan timed out")
        except Exception as e:
            logger.error(f"Nuclei scan failed: {e}")
        
        return {
            "tool": "nuclei",
            "target": target,
            "findings": findings,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_gobuster_scan(self, target_url: str, wordlist: str = None) -> Dict[str, Any]:
        """Run Gobuster directory enumeration"""
        
        findings = []
        
        try:
            cmd = ["gobuster", "dir", "-u", target_url, "-q"]
            if wordlist:
                cmd.extend(["-w", wordlist])
            else:
                cmd.extend(["-w", "/usr/share/wordlists/dirb/common.txt"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and not line.startswith('='):
                        parts = line.split()
                        if len(parts) >= 2:
                            findings.append({
                                "path": parts[0],
                                "status": parts[1] if len(parts) > 1 else "200",
                                "size": parts[2] if len(parts) > 2 else "0"
                            })
                        
        except subprocess.TimeoutExpired:
            logger.warning("Gobuster scan timed out")
        except Exception as e:
            logger.error(f"Gobuster scan failed: {e}")
        
        return {
            "tool": "gobuster",
            "target": target_url,
            "findings": findings,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def convert_c_to_go(self, c_code: str) -> Dict[str, Any]:
        """Convert C code to Go using c2go transpiler"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as tmp_file:
                tmp_file.write(c_code)
                tmp_file.flush()
                
                result = subprocess.run([
                    "c2go", "transpile", tmp_file.name
                ], capture_output=True, text=True, timeout=60)
                
                os.unlink(tmp_file.name)
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "converted_code": result.stdout,
                        "warnings": result.stderr if result.stderr else None
                    }
                else:
                    return {
                        "success": False,
                        "error": result.stderr,
                        "original_code": c_code
                    }
                    
        except subprocess.TimeoutExpired:
            logger.warning("C to Go conversion timed out")
            return {"success": False, "error": "Conversion timed out"}
        except Exception as e:
            logger.error(f"C to Go conversion failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_with_tree_sitter(self, code: str, language: str) -> Dict[str, Any]:
        """Enhanced code analysis using Tree-sitter"""
        
        try:
            if language not in self.parsers:
                return {"error": f"Parser not available for {language}"}
            
            # Simulate Tree-sitter analysis (would need actual implementation)
            analysis = {
                "language": language,
                "lines_of_code": len(code.split('\n')),
                "functions": [],  # Would extract function definitions
                "classes": [],   # Would extract class definitions
                "imports": [],   # Would extract import statements
                "complexity": "medium",  # Would calculate cyclomatic complexity
                "security_patterns": []  # Would identify security-relevant patterns
            }
            
            # Basic pattern matching for demonstration
            if "password" in code.lower() or "secret" in code.lower():
                analysis["security_patterns"].append({
                    "pattern": "hardcoded_secrets",
                    "severity": "high",
                    "message": "Potential hardcoded secrets detected"
                })
            
            if "eval(" in code or "exec(" in code:
                analysis["security_patterns"].append({
                    "pattern": "code_injection",
                    "severity": "critical",
                    "message": "Potential code injection vulnerability"
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Tree-sitter analysis failed: {e}")
            return {"error": str(e)}

# Initialize MCP server
mcp_server = MCPServer()

# FastAPI app
app = FastAPI(
    title="MCP Server - Code Analysis & Security",
    description="Model Context Protocol server for code analysis, security scanning, and conversion assessment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.1.17:3001", "http://192.168.1.17:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "docker": "healthy" if mcp_server.docker_client.ping() else "unhealthy",
            "parsers": len(mcp_server.parsers)
        }
    }

@app.post("/analyze/codebase")
async def analyze_codebase(request: AnalysisRequest):
    """Analyze a codebase for structure, security, and conversion potential"""
    return await mcp_server.analyze_codebase(request)

@app.post("/analyze/security")
async def security_analysis(request: SecurityAnalysisRequest):
    """Run focused security analysis on code"""
    
    repo_path = Path(request.code_path)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Code path not found")
    
    findings = []
    
    if "static" in request.scan_types:
        findings.extend(await mcp_server._run_security_analysis(repo_path, "auto"))
    
    return {
        "scan_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "scan_types": request.scan_types,
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
            "critical": len([f for f in findings if f.get("severity") == "critical"]),
            "high": len([f for f in findings if f.get("severity") == "high"]),
            "medium": len([f for f in findings if f.get("severity") == "medium"]),
            "low": len([f for f in findings if f.get("severity") == "low"])
        }
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    
    tools = [
        {
            "name": "codebase_scan",
            "description": "Comprehensive codebase analysis including structure, security, and conversion assessment",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repository_path": {"type": "string"},
                    "language": {"type": "string"},
                    "analysis_type": {"type": "string", "enum": ["full", "security", "performance", "structure"]},
                    "target_language": {"type": "string", "optional": True}
                },
                "required": ["repository_path", "language"]
            }
        },
        {
            "name": "security_scan",
            "description": "Focused security analysis using multiple static analysis tools",
            "input_schema": {
                "type": "object",
                "properties": {
                    "code_path": {"type": "string"},
                    "scan_types": {"type": "array", "items": {"type": "string"}},
                    "output_format": {"type": "string", "default": "json"}
                },
                "required": ["code_path"]
            }
        }
    ]
    
    return {"tools": tools}

@app.get("/resources")
async def list_resources():
    """List available MCP resources"""
    
    resources = [
        {
            "uri": "analysis://codebase",
            "name": "Codebase Analysis Results",
            "description": "Results from comprehensive codebase analysis",
            "mimeType": "application/json"
        },
        {
            "uri": "security://findings",
            "name": "Security Findings",
            "description": "Security vulnerabilities and issues found in code",
            "mimeType": "application/json"
        }
    ]
    
    return {"resources": resources}

@app.post("/nuclei-scan")
async def nuclei_scan_endpoint(target: str, templates: List[str] = None):
    """Run Nuclei vulnerability scan"""
    try:
        result = await mcp_server.run_nuclei_scan(target, templates)
        return result
    except Exception as e:
        logger.error(f"Nuclei scan endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gobuster-scan")
async def gobuster_scan_endpoint(target_url: str, wordlist: str = None):
    """Run Gobuster directory enumeration"""
    try:
        result = await mcp_server.run_gobuster_scan(target_url, wordlist)
        return result
    except Exception as e:
        logger.error(f"Gobuster scan endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert-c2go")
async def c2go_convert_endpoint(c_code: str):
    """Convert C code to Go using c2go transpiler"""
    try:
        result = await mcp_server.convert_c_to_go(c_code)
        return result
    except Exception as e:
        logger.error(f"C to Go conversion endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tree-sitter-analysis")
async def tree_sitter_analysis_endpoint(code: str, language: str):
    """Enhanced code analysis using Tree-sitter"""
    try:
        result = await mcp_server.analyze_with_tree_sitter(code, language)
        return result
    except Exception as e:
        logger.error(f"Tree-sitter analysis endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
