#!/usr/bin/env python3
"""
SkyQ Enhanced Discovery Script - Updated for Current Integration

Compatible with uc-intg-skyq integration architecture.
Discovers all available SkyQ API endpoints and remote commands.

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import json
import socket
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import traceback


class SkyQEnhancedDiscovery:
    """Enhanced discovery for complete SkyQ API mapping - Updated for current integration."""
    
    def __init__(self, device_ip: str, rest_port: int = 9006, remote_port: int = 49160):
        """Initialize enhanced discovery with configurable ports."""
        self.device_ip = device_ip
        self.rest_port = rest_port
        self.remote_port = remote_port
        self.discovery_report = {
            "device_ip": device_ip,
            "rest_port": rest_port,
            "remote_port": remote_port,
            "discovery_timestamp": datetime.now().isoformat(),
            "integration_version": "1.0.0",
            "upnp_analysis": {},
            "comprehensive_http_scan": {},
            "complete_remote_commands": {},
            "api_capabilities": {},
            "integration_blueprint": {},
            "current_integration_commands": [],
            "errors": []
        }
        
        # Current integration command set (from actual integration files)
        self.current_integration_commands = {
            # Power commands (4/4 working from current integration)
            "power": "power",
            "standby": "standby", 
            "on": "on",
            "off": "off",
            
            # Navigation commands (8/8 working from current integration)
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "select": "select",
            "back": "back",
            "home": "home",
            "menu": "menu",
            
            # Playback commands (6/6 working from current integration)
            "play": "play",
            "pause": "pause",
            "stop": "stop",
            "record": "record",
            "rewind": "rewind",
            "fast_forward": "fastforward",
            
            # Channel commands (working ones only)
            "channel_up": "channelup",
            "guide": "guide",
            "info": "info",
            # EXCLUDED: channeldown (fails per discovery)
            
            # Number commands (10/10 working from current integration)
            "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
            
            # Color commands (4/4 working from current integration)
            "red": "red",
            "green": "green",
            "yellow": "yellow",
            "blue": "blue",
            
            # Volume commands (3/3 working from current integration)
            "volume_up": "volumeup",
            "volume_down": "volumedown",
            "mute": "mute",
            
            # Special commands (working ones only)
            "sky": "sky",
            "search": "search",
            "text": "text",
            "help": "help",
            "services": "services"
            # EXCLUDED: interactive (fails per discovery)
        }
        
    def run_enhanced_discovery(self) -> Dict[str, Any]:
        """Run comprehensive enhanced discovery."""
        print("SkyQ Enhanced Discovery - Current Integration Compatible")
        print("=" * 65)
        print(f"Target Device: {self.device_ip}:{self.rest_port}")
        print(f"Remote Port: {self.remote_port}")
        print(f"Current Integration Commands: {len(self.current_integration_commands)}")
        print("Goal: Verify and discover additional SkyQ capabilities")
        print()
        
        try:
            # Phase 1: UPnP Deep Analysis
            print("Phase 1: UPnP Device Description Analysis")
            self._analyze_upnp_description()
            
            # Phase 2: Comprehensive HTTP Endpoint Discovery
            print("\nPhase 2: Comprehensive HTTP Endpoint Scan")
            self._comprehensive_http_discovery()
            
            # Phase 3: Current Integration Command Verification
            print("\nPhase 3: Current Integration Command Verification")
            self._verify_current_integration_commands()
            
            # Phase 4: Additional Command Discovery
            print("\nPhase 4: Additional Command Discovery")
            self._discover_additional_commands()
            
            # Phase 5: API Capability Analysis
            print("\nPhase 5: API Capability Analysis")
            self._analyze_api_capabilities()
            
            # Phase 6: Integration Blueprint Update
            print("\nPhase 6: Generate Updated Integration Blueprint")
            self._generate_integration_blueprint()
            
        except Exception as e:
            error_msg = f"Enhanced discovery failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.discovery_report["errors"].append(error_msg)
            self.discovery_report["errors"].append(traceback.format_exc())
        
        return self.discovery_report
    
    def _analyze_upnp_description(self):
        """Analyze the UPnP device description."""
        upnp_analysis = {
            "description_url": f"http://{self.device_ip}:49153/description3.xml",
            "device_info": {},
            "services": [],
            "control_urls": [],
            "capabilities": []
        }
        
        try:
            print(f"   Fetching UPnP description from port 49153...")
            
            with urllib.request.urlopen(upnp_analysis["description_url"], timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                print(f"      Retrieved {len(content)} bytes of UPnP description")
                
                # Store raw description for analysis
                upnp_analysis["raw_description"] = content
                
                # Extract device information
                device_info = self._extract_upnp_device_info(content)
                upnp_analysis["device_info"] = device_info
                
                # Extract services and control URLs
                services = self._extract_upnp_services(content)
                upnp_analysis["services"] = services
                
                print(f"      Found {len(services)} UPnP services")
                
        except Exception as e:
            print(f"      UPnP analysis failed: {e}")
            upnp_analysis["error"] = str(e)
        
        self.discovery_report["upnp_analysis"] = upnp_analysis
    
    def _extract_upnp_device_info(self, content: str) -> Dict[str, str]:
        """Extract device info from UPnP description."""
        device_info = {}
        
        # Extract device information tags
        info_tags = [
            "friendlyName", "manufacturer", "manufacturerURL", 
            "modelDescription", "modelName", "modelNumber", "modelURL",
            "serialNumber", "UDN", "deviceType"
        ]
        
        for tag in info_tags:
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            
            start_pos = content.find(start_tag)
            if start_pos != -1:
                start_pos += len(start_tag)
                end_pos = content.find(end_tag, start_pos)
                if end_pos != -1:
                    device_info[tag] = content[start_pos:end_pos].strip()
        
        return device_info
    
    def _extract_upnp_services(self, content: str) -> List[Dict[str, str]]:
        """Extract service information from UPnP description."""
        services = []
        
        # Find all service blocks
        service_start = 0
        while True:
            service_start = content.find("<service>", service_start)
            if service_start == -1:
                break
            
            service_end = content.find("</service>", service_start)
            if service_end == -1:
                break
            
            service_block = content[service_start:service_end + 10]
            
            # Extract service info
            service_info = {}
            service_tags = ["serviceType", "serviceId", "controlURL", "eventSubURL", "SCPDURL"]
            
            for tag in service_tags:
                start_tag = f"<{tag}>"
                end_tag = f"</{tag}>"
                
                start_pos = service_block.find(start_tag)
                if start_pos != -1:
                    start_pos += len(start_tag)
                    end_pos = service_block.find(end_tag, start_pos)
                    if end_pos != -1:
                        service_info[tag] = service_block[start_pos:end_pos].strip()
            
            if service_info:
                services.append(service_info)
            
            service_start = service_end
        
        return services
    
    def _comprehensive_http_discovery(self):
        """Comprehensive HTTP endpoint discovery with current integration focus."""
        http_analysis = {
            "endpoint_patterns_tested": 0,
            "working_endpoints": {},
            "endpoint_categories": {},
            "api_patterns": {},
            "current_integration_endpoints": {}
        }
        
        # Known working endpoints from current integration
        current_endpoints = [
            "/as/services",           # Channel list - CONFIRMED WORKING
            "/as/system/information", # Device info - CONFIRMED WORKING
            "/as/system/status",      # Status info - ADDED in current integration
        ]
        
        # Additional endpoints to test based on SkyQ patterns
        test_endpoints = [
            "/as/system",
            "/as/system/state",
            "/as/status", 
            "/as/current",
            "/as/media",
            "/as/media/current",
            "/as/media/status",
            "/as/pvr",
            "/as/pvr/recordings",
            "/as/pvr/current",
            "/as/recordings",
            "/as/epg",
            "/as/epg/current",
            "/as/channels",
            "/as/channels/current",
            "/as/device",
            "/as/device/status",
            "/as/transport",
            "/as/transport/status"
        ]
        
        print(f"   Testing current integration endpoints...")
        for endpoint in current_endpoints:
            result = self._test_http_endpoint(endpoint)
            if result.get("accessible"):
                http_analysis["current_integration_endpoints"][endpoint] = result
                http_analysis["working_endpoints"][endpoint] = result
                print(f"      SUCCESS: {endpoint} - HTTP {result['status_code']}")
            else:
                print(f"      FAILED: {endpoint} - {result.get('error', 'Unknown error')}")
        
        print(f"   Testing additional potential endpoints...")
        for endpoint in test_endpoints:
            if endpoint not in current_endpoints:  # Don't retest current ones
                result = self._test_http_endpoint(endpoint)
                if result.get("accessible"):
                    http_analysis["working_endpoints"][endpoint] = result
                    print(f"      NEW: {endpoint} - HTTP {result['status_code']}")
        
        http_analysis["endpoint_patterns_tested"] = len(current_endpoints) + len(test_endpoints)
        
        print(f"   SUMMARY: {len(http_analysis['working_endpoints'])} working HTTP endpoints found")
        print(f"   Current integration: {len(http_analysis['current_integration_endpoints'])}/{len(current_endpoints)} working")
        
        self.discovery_report["comprehensive_http_scan"] = http_analysis
    
    def _test_http_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Test single HTTP endpoint with detailed analysis."""
        try:
            url = f"http://{self.device_ip}:{self.rest_port}{endpoint}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SkyQ-Integration-Discovery/1.0')
            
            with urllib.request.urlopen(req, timeout=8) as response:
                content = response.read()
                headers = dict(response.headers)
                
                # Analyze content
                content_analysis = {}
                if content:
                    content_text = content.decode('utf-8', errors='ignore')
                    content_analysis = {
                        "length": len(content),
                        "type": "json" if "application/json" in headers.get('Content-Type', '') else "other",
                        "preview": content_text[:300] if len(content_text) > 300 else content_text,
                        "contains_sky_keywords": any(kw in content_text.lower() for kw in ['sky', 'channel', 'service', 'recording', 'device'])
                    }
                
                return {
                    "accessible": True,
                    "status_code": response.getcode(),
                    "headers": headers,
                    "content_analysis": content_analysis
                }
                
        except urllib.error.HTTPError as e:
            return {
                "accessible": False,
                "error": f"HTTP {e.code}: {e.reason}",
                "status_code": e.code
            }
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e)
            }
    
    def _verify_current_integration_commands(self):
        """Verify all commands used in current integration work correctly."""
        verification_results = {
            "total_commands": len(self.current_integration_commands),
            "verified_working": [],
            "verification_failed": [],
            "command_details": {}
        }
        
        print(f"   Verifying {len(self.current_integration_commands)} current integration commands...")
        
        for cmd_name, skyq_command in self.current_integration_commands.items():
            try:
                result = self._test_remote_command(skyq_command)
                verification_results["command_details"][cmd_name] = result
                
                if result.get("success"):
                    verification_results["verified_working"].append(cmd_name)
                    response = result.get("response_text", "").strip()
                    print(f"      VERIFIED: {cmd_name} -> {skyq_command} (Response: {response})")
                else:
                    verification_results["verification_failed"].append(cmd_name)
                    error = result.get("error", "Unknown error")
                    print(f"      FAILED: {cmd_name} -> {skyq_command} (Error: {error})")
                    
            except Exception as e:
                verification_results["verification_failed"].append(cmd_name)
                verification_results["command_details"][cmd_name] = {"error": str(e)}
                print(f"      ERROR: {cmd_name} -> {skyq_command} (Exception: {e})")
        
        print(f"   VERIFICATION SUMMARY: {len(verification_results['verified_working'])}/{len(self.current_integration_commands)} commands working")
        
        self.discovery_report["current_integration_verification"] = verification_results
        self.discovery_report["current_integration_commands"] = list(self.current_integration_commands.keys())
    
    def _discover_additional_commands(self):
        """Discover additional commands not in current integration."""
        additional_analysis = {
            "tested_commands": [],
            "new_working_commands": [],
            "command_details": {}
        }
        
        # Commands to test that might work but aren't in current integration
        additional_commands = [
            # Potentially missing commands
            "tv", "radio", "interactive", "boxoffice", "mysky", "planner",
            "backup", "top", "i", "tvguide", "channeldown", "subtitle", 
            "audio", "dismiss", "announce", "boxoffice", "tvguide"
        ]
        
        print(f"   Testing {len(additional_commands)} additional potential commands...")
        
        for command in additional_commands:
            if command not in self.current_integration_commands.values():  # Don't retest current ones
                try:
                    result = self._test_remote_command(command)
                    additional_analysis["command_details"][command] = result
                    additional_analysis["tested_commands"].append(command)
                    
                    if result.get("success"):
                        additional_analysis["new_working_commands"].append(command)
                        response = result.get("response_text", "").strip()
                        print(f"      NEW COMMAND: {command} (Response: {response})")
                    
                except Exception as e:
                    additional_analysis["command_details"][command] = {"error": str(e)}
        
        print(f"   ADDITIONAL COMMANDS: {len(additional_analysis['new_working_commands'])} new working commands found")
        
        self.discovery_report["additional_command_discovery"] = additional_analysis
    
    def _test_remote_command(self, command: str) -> Dict[str, Any]:
        """Test a single remote command using current integration protocol."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device_ip, self.remote_port))
            
            # Use current integration format: command + newline
            command_bytes = f"{command}\n".encode('utf-8')
            sock.send(command_bytes)
            
            # Try to get response
            sock.settimeout(3)
            response = sock.recv(256)
            
            sock.close()
            
            return {
                "success": True,
                "command": command,
                "command_hex": command_bytes.hex(),
                "response_hex": response.hex() if response else None,
                "response_length": len(response) if response else 0,
                "response_text": response.decode('utf-8', errors='ignore') if response else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    def _analyze_api_capabilities(self):
        """Analyze discovered API capabilities against current integration needs."""
        capabilities = {
            "http_api": {},
            "remote_control": {},
            "current_integration_status": {},
            "missing_capabilities": [],
            "integration_readiness": {}
        }
        
        # Analyze HTTP API capabilities
        http_endpoints = self.discovery_report.get("comprehensive_http_scan", {}).get("working_endpoints", {})
        current_endpoints = self.discovery_report.get("comprehensive_http_scan", {}).get("current_integration_endpoints", {})
        
        capabilities["http_api"] = {
            "total_endpoints": len(http_endpoints),
            "current_integration_endpoints": len(current_endpoints),
            "working_current_endpoints": list(current_endpoints.keys()),
            "additional_endpoints": [ep for ep in http_endpoints.keys() if ep not in current_endpoints]
        }
        
        # Analyze remote control capabilities
        verification = self.discovery_report.get("current_integration_verification", {})
        additional = self.discovery_report.get("additional_command_discovery", {})
        
        capabilities["remote_control"] = {
            "current_integration_commands": verification.get("total_commands", 0),
            "verified_working": len(verification.get("verified_working", [])),
            "verification_failed": len(verification.get("verification_failed", [])),
            "additional_commands_found": len(additional.get("new_working_commands", [])),
            "total_working_commands": len(verification.get("verified_working", [])) + len(additional.get("new_working_commands", []))
        }
        
        # Current integration status
        capabilities["current_integration_status"] = {
            "http_endpoints_working": len(current_endpoints) > 0,
            "essential_endpoints_available": "/as/services" in current_endpoints and "/as/system/information" in current_endpoints,
            "remote_commands_working": verification.get("total_commands", 0) > 0,
            "command_success_rate": len(verification.get("verified_working", [])) / max(verification.get("total_commands", 1), 1) * 100
        }
        
        # Integration readiness assessment for current integration
        readiness_score = 0
        max_score = 100
        
        # HTTP API score (30 points max)
        if "/as/services" in current_endpoints:
            readiness_score += 15  # Essential channel data
        if "/as/system/information" in current_endpoints:
            readiness_score += 10  # Essential device info
        readiness_score += min(len(http_endpoints), 5)  # Additional endpoints (1 point each, max 5)
        
        # Remote control score (70 points max)
        command_success_rate = capabilities["current_integration_status"]["command_success_rate"]
        readiness_score += (command_success_rate / 100) * 70
        
        capabilities["integration_readiness"] = {
            "score": int(readiness_score),
            "max_score": max_score,
            "percentage": int(readiness_score),
            "current_integration_compatible": readiness_score >= 80
        }
        
        print(f"   Current Integration Readiness: {capabilities['integration_readiness']['percentage']}%")
        print(f"   HTTP endpoints: {len(current_endpoints)}/{len(http_endpoints)} current working")
        print(f"   Remote commands: {capabilities['remote_control']['verified_working']}/{capabilities['remote_control']['current_integration_commands']} verified")
        
        self.discovery_report["api_capabilities"] = capabilities
    
    def _generate_integration_blueprint(self):
        """Generate integration blueprint based on current integration architecture."""
        blueprint = {
            "integration_approach": "current_architecture_compatible",
            "confidence_level": "high",
            "current_integration_status": "verified",
            "implementation_plan": {},
            "verified_endpoints": {},
            "verified_commands": {},
            "recommended_updates": [],
            "additional_opportunities": []
        }
        
        # Get verification results
        verification = self.discovery_report.get("current_integration_verification", {})
        http_scan = self.discovery_report.get("comprehensive_http_scan", {})
        additional = self.discovery_report.get("additional_command_discovery", {})
        capabilities = self.discovery_report.get("api_capabilities", {})
        
        # Current integration implementation plan
        blueprint["implementation_plan"] = {
            "architecture": "Dual HTTP + TCP client (verified working)",
            "http_endpoints": "Real SkyQ REST API on port " + str(self.rest_port),
            "remote_control": "Native SkyQ TCP protocol on port " + str(self.remote_port),
            "entity_strategy": "Media Player + Remote entities per device",
            "multi_device_support": "Full multi-device configuration"
        }
        
        # Verified working endpoints
        current_endpoints = http_scan.get("current_integration_endpoints", {})
        blueprint["verified_endpoints"] = {
            endpoint: {
                "status": "working",
                "http_code": details.get("status_code"),
                "integration_use": self._get_endpoint_use(endpoint)
            }
            for endpoint, details in current_endpoints.items()
        }
        
        # Verified working commands
        working_commands = verification.get("verified_working", [])
        blueprint["verified_commands"] = {
            "total_working": len(working_commands),
            "command_categories": self._categorize_commands(working_commands),
            "failed_commands": verification.get("verification_failed", [])
        }
        
        # Recommendations based on discovery
        recommendations = []
        
        # Check for missing endpoints
        if "/as/system/status" not in current_endpoints:
            recommendations.append({
                "type": "endpoint_missing", 
                "issue": "/as/system/status endpoint not working",
                "impact": "Limited system status information",
                "action": "Use fallback status detection via /as/services"
            })
        
        # Check for failed commands
        if verification.get("verification_failed"):
            recommendations.append({
                "type": "command_verification", 
                "issue": f"{len(verification.get('verification_failed', []))} commands failed verification",
                "commands": verification.get("verification_failed", []),
                "action": "Remove failed commands or investigate device-specific issues"
            })
        
        # Check for new opportunities
        new_commands = additional.get("new_working_commands", [])
        if new_commands:
            recommendations.append({
                "type": "new_commands_available", 
                "issue": f"{len(new_commands)} additional working commands discovered",
                "commands": new_commands,
                "action": "Consider adding to integration for enhanced functionality"
            })
        
        blueprint["recommended_updates"] = recommendations
        
        # Set confidence level based on verification results
        success_rate = capabilities.get("current_integration_status", {}).get("command_success_rate", 0)
        if success_rate >= 90:
            blueprint["confidence_level"] = "high"
        elif success_rate >= 75:
            blueprint["confidence_level"] = "medium"
        else:
            blueprint["confidence_level"] = "low"
        
        print(f"   Integration Status: {blueprint['current_integration_status']}")
        print(f"   Confidence Level: {blueprint['confidence_level']}")
        print(f"   Verified Commands: {len(working_commands)}")
        print(f"   Recommendations: {len(recommendations)}")
        
        self.discovery_report["integration_blueprint"] = blueprint
    
    def _get_endpoint_use(self, endpoint: str) -> str:
        """Get the integration use case for an endpoint."""
        use_cases = {
            "/as/services": "Channel list and service information",
            "/as/system/information": "Device model, serial, and hardware info",
            "/as/system/status": "Real-time device and playback status"
        }
        return use_cases.get(endpoint, "Unknown use case")
    
    def _categorize_commands(self, commands: List[str]) -> Dict[str, List[str]]:
        """Categorize commands by function."""
        categories = {
            "power": ["power", "standby", "on", "off"],
            "navigation": ["up", "down", "left", "right", "select", "back", "home", "menu"],
            "playbook": ["play", "pause", "stop", "record", "rewind", "fast_forward"],
            "channels": ["channel_up", "guide", "info"],
            "numbers": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            "colors": ["red", "green", "yellow", "blue"],
            "volume": ["volume_up", "volume_down", "mute"],
            "special": ["sky", "search", "text", "help", "services"]
        }
        
        categorized = {}
        for category, category_commands in categories.items():
            working_in_category = [cmd for cmd in commands if cmd in category_commands]
            if working_in_category:
                categorized[category] = working_in_category
        
        return categorized
    
    def save_enhanced_report(self, filename: Optional[str] = None) -> str:
        """Save enhanced discovery report with timestamp."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"skyq_enhanced_discovery_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_report, f, indent=2, default=str)
            return filename
        except Exception as e:
            print(f"ERROR: Failed to save report: {e}")
            return ""


def main():
    """Main function for enhanced discovery."""
    if len(sys.argv) > 1:
        device_ip = sys.argv[1]
    else:
        device_ip = input("Enter SkyQ device IP address: ").strip()
        if not device_ip:
            print("ERROR: No IP address provided")
            sys.exit(1)
    
    # Optional port configuration
    rest_port = 9006
    remote_port = 49160
    
    if len(sys.argv) > 2:
        try:
            rest_port = int(sys.argv[2])
        except ValueError:
            print(f"WARNING: Invalid REST port '{sys.argv[2]}', using default 9006")
    
    try:
        print("SkyQ Enhanced Discovery - Current Integration Compatible")
        print("=" * 60)
        print(f"Target Device: {device_ip}:{rest_port}")
        print(f"Remote Port: {remote_port}")
        print("Purpose: Verify current integration and discover additional capabilities")
        print()
        
        # Run enhanced discovery
        discovery = SkyQEnhancedDiscovery(device_ip, rest_port, remote_port)
        results = discovery.run_enhanced_discovery()
        
        # Save comprehensive report
        report_file = discovery.save_enhanced_report()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("DISCOVERY COMPLETE - CURRENT INTEGRATION ANALYSIS")
        print("=" * 60)
        
        # Print key findings
        verification = results.get("current_integration_verification", {})
        capabilities = results.get("api_capabilities", {})
        blueprint = results.get("integration_blueprint", {})
        
        print("CURRENT INTEGRATION STATUS:")
        working_commands = len(verification.get("verified_working", []))
        total_commands = verification.get("total_commands", 0)
        success_rate = working_commands / max(total_commands, 1) * 100
        
        print(f"   Commands: {working_commands}/{total_commands} working ({success_rate:.1f}%)")
        
        current_endpoints = capabilities.get("http_api", {}).get("current_integration_endpoints", 0)
        print(f"   HTTP Endpoints: {current_endpoints} essential endpoints working")
        
        readiness = capabilities.get("integration_readiness", {})
        if readiness:
            print(f"   Integration Readiness: {readiness.get('percentage', 0)}%")
        
        # Print recommendations
        recommendations = blueprint.get("recommended_updates", [])
        if recommendations:
            print(f"\nRECOMMENDATIONS ({len(recommendations)}):")
            for rec in recommendations:
                print(f"   - {rec.get('issue', 'Unknown issue')}")
        
        # Print additional discoveries
        additional = results.get("additional_command_discovery", {})
        new_commands = additional.get("new_working_commands", [])
        if new_commands:
            print(f"\nNEW COMMANDS DISCOVERED: {len(new_commands)}")
            for cmd in new_commands:
                print(f"   + {cmd}")
        
        if report_file:
            print(f"\nFULL REPORT SAVED: {report_file}")
            print("Send this file to: meir.miyara@gmail.com")
        
        print(f"\nUSAGE: python skyq_discovery_v2.py [IP_ADDRESS] [REST_PORT]")
        print("Example: python skyq_discovery_v2.py 192.168.1.100 9006")
        
    except KeyboardInterrupt:
        print("\n\nDiscovery cancelled by user")
    except Exception as e:
        print(f"\n\nERROR: Unexpected error: {e}")
        traceback.print_exc()
    
    finally:
        try:
            input("\nPress ENTER to exit...")
        except:
            pass


if __name__ == "__main__":
    main()