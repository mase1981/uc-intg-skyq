#!/usr/bin/env python3
"""
Enhanced SkyQ Discovery Script - Tests both Direct TCP and pyskyqremote compatibility

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import json
import socket
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import sys
import traceback


class EnhancedSkyQDiscovery:
    """Enhanced discovery with both TCP and pyskyqremote testing."""
    
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
            "integration_version": "1.0.17",
            "device_analysis": {},
            "tcp_command_verification": {},
            "pyskyqremote_verification": {},
            "command_compatibility_matrix": {},
            "integration_recommendations": {},
            "errors": []
        }
        
        # All commands to test
        self.all_commands = [
            # Original 43 commands
            "power", "standby", "on", "off", "up", "down", "left", "right", 
            "select", "back", "home", "menu", "play", "pause", "stop", 
            "record", "fastforward", "rewind", "channelup", "guide", "info",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "red", "green", "yellow", "blue", "volumeup", "volumedown", "mute",
            "sky", "search", "text", "help", "services",
            # Additional discovered commands
            "channeldown", "tvguide", "i", "boxoffice", "dismiss", "backup",
            "tv", "radio", "interactive", "mysky", "planner", "top", 
            "subtitle", "audio", "announce", "last", "list"
        ]
        
    def run_discovery(self) -> Dict[str, Any]:
        """Run comprehensive discovery with both TCP and pyskyqremote testing."""
        print("Enhanced SkyQ Discovery - TCP + pyskyqremote Testing")
        print("=" * 60)
        print(f"Target Device: {self.device_ip}:{self.rest_port}")
        print(f"Remote Port: {self.remote_port}")
        print(f"Commands to Test: {len(self.all_commands)}")
        print()
        
        try:
            # Phase 1: Device Analysis
            print("Phase 1: Device Information Analysis")
            self._analyze_device_info()
            
            # Phase 2: Direct TCP Command Testing
            print("\nPhase 2: Direct TCP Command Testing")
            self._test_tcp_commands()
            
            # Phase 3: pyskyqremote Command Testing
            print("\nPhase 3: pyskyqremote Command Testing")
            self._test_pyskyqremote_commands()
            
            # Phase 4: Command Compatibility Analysis
            print("\nPhase 4: Command Compatibility Analysis")
            self._analyze_command_compatibility()
            
            # Phase 5: Integration Recommendations
            print("\nPhase 5: Generate Integration Recommendations")
            self._generate_integration_recommendations()
            
        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.discovery_report["errors"].append(error_msg)
            self.discovery_report["errors"].append(traceback.format_exc())
        
        return self.discovery_report
    
    def _analyze_device_info(self):
        """Analyze device information and connectivity."""
        device_analysis = {
            "http_connectivity": {},
            "tcp_connectivity": {},
            "device_info": {},
            "pyskyqremote_availability": {}
        }
        
        print(f"   Testing HTTP connectivity on port {self.rest_port}...")
        http_result = self._test_http_connectivity()
        device_analysis["http_connectivity"] = http_result
        
        print(f"   Testing TCP connectivity on port {self.remote_port}...")
        tcp_result = self._test_tcp_connectivity()
        device_analysis["tcp_connectivity"] = tcp_result
        
        print(f"   Retrieving device information...")
        device_info = self._get_device_information()
        device_analysis["device_info"] = device_info
        
        print(f"   Testing pyskyqremote availability...")
        pyskyq_avail = self._test_pyskyqremote_availability()
        device_analysis["pyskyqremote_availability"] = pyskyq_avail
        
        if device_info.get("success"):
            model = device_info.get("model", "Unknown")
            serial = device_info.get("serial", "Unknown")
            print(f"      Device: {model} (Serial: {serial})")
        
        self.discovery_report["device_analysis"] = device_analysis
    
    def _test_http_connectivity(self) -> Dict[str, Any]:
        """Test HTTP connectivity and basic endpoints."""
        try:
            url = f"http://{self.device_ip}:{self.rest_port}/as/system/information"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SkyQ-Discovery/1.0')
            
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=10) as response:
                response_time = time.time() - start_time
                content = response.read()
                
                return {
                    "success": True,
                    "status_code": response.getcode(),
                    "response_time_ms": int(response_time * 1000),
                    "content_length": len(content),
                    "headers": dict(response.headers)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_tcp_connectivity(self) -> Dict[str, Any]:
        """Test TCP remote control connectivity."""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device_ip, self.remote_port))
            connect_time = time.time() - start_time
            
            # Test with a simple command
            test_command = "up\n"
            sock.send(test_command.encode('utf-8'))
            
            # Try to receive response
            sock.settimeout(3)
            response = sock.recv(256)
            total_time = time.time() - start_time
            
            sock.close()
            
            return {
                "success": True,
                "connect_time_ms": int(connect_time * 1000),
                "total_time_ms": int(total_time * 1000),
                "test_response": response.decode('utf-8', errors='ignore').strip()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_device_information(self) -> Dict[str, Any]:
        """Get comprehensive device information."""
        try:
            url = f"http://{self.device_ip}:{self.rest_port}/as/system/information"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
                data = json.loads(content.decode('utf-8'))
                
                return {
                    "success": True,
                    "model": data.get("hardwareModel", "Unknown"),
                    "serial": data.get("serialNumber", "Unknown"),
                    "software_version": data.get("ASVersion", "Unknown"),
                    "mac_address": data.get("MACAddress", "Unknown"),
                    "ip_address": data.get("IPAddress", "Unknown"),
                    "raw_data": data
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_pyskyqremote_availability(self) -> Dict[str, Any]:
        """Test if pyskyqremote can connect to device."""
        try:
            from pyskyqremote.skyq_remote import SkyQRemote
            
            print("      Attempting pyskyqremote connection...")
            start_time = time.time()
            skyq_remote = SkyQRemote(self.device_ip)
            connection_time = time.time() - start_time
            
            if skyq_remote and skyq_remote.device_setup:
                device_info = skyq_remote.get_device_information()
                return {
                    "success": True,
                    "connection_time_ms": int(connection_time * 1000),
                    "device_setup": True,
                    "device_info_available": device_info is not None,
                    "library_version": getattr(skyq_remote, 'version', 'unknown')
                }
            else:
                return {
                    "success": False,
                    "connection_time_ms": int(connection_time * 1000),
                    "device_setup": False,
                    "error": "Device setup failed"
                }
                
        except ImportError:
            return {
                "success": False,
                "error": "pyskyqremote library not available"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_tcp_commands(self):
        """Test all commands via direct TCP."""
        tcp_verification = {
            "total_tested": len(self.all_commands),
            "working": [],
            "failed": [],
            "command_details": {}
        }
        
        print(f"   Testing {len(self.all_commands)} commands via direct TCP...")
        
        for i, command in enumerate(self.all_commands):
            print(f"      [{i+1:2d}/{len(self.all_commands)}] TCP Testing: {command}")
            
            result = self._test_tcp_command(command)
            tcp_verification["command_details"][command] = result
            
            if result["success"]:
                tcp_verification["working"].append(command)
                timing = result.get("timing_ms", 0)
                print(f"          ✓ Success ({timing}ms)")
            else:
                tcp_verification["failed"].append(command)
                error = result.get("error", "Unknown error")
                print(f"          ✗ Failed: {error}")
            
            time.sleep(0.1)
        
        success_rate = len(tcp_verification["working"]) / len(self.all_commands) * 100
        print(f"   TCP SUMMARY: {len(tcp_verification['working'])}/{len(self.all_commands)} commands working ({success_rate:.1f}%)")
        
        self.discovery_report["tcp_command_verification"] = tcp_verification
    
    def _test_pyskyqremote_commands(self):
        """Test all commands via pyskyqremote library."""
        pyskyq_verification = {
            "library_available": False,
            "total_tested": len(self.all_commands),
            "working": [],
            "failed": [],
            "command_details": {}
        }
        
        try:
            from pyskyqremote.skyq_remote import SkyQRemote
            skyq_remote = SkyQRemote(self.device_ip)
            
            if not skyq_remote or not skyq_remote.device_setup:
                pyskyq_verification["error"] = "Could not establish pyskyqremote connection"
                self.discovery_report["pyskyqremote_verification"] = pyskyq_verification
                print("   pyskyqremote connection failed, skipping library tests")
                return
            
            pyskyq_verification["library_available"] = True
            print(f"   Testing {len(self.all_commands)} commands via pyskyqremote...")
            
            for i, command in enumerate(self.all_commands):
                print(f"      [{i+1:2d}/{len(self.all_commands)}] pyskyqremote Testing: {command}")
                
                result = self._test_pyskyqremote_command(skyq_remote, command)
                pyskyq_verification["command_details"][command] = result
                
                if result["success"]:
                    pyskyq_verification["working"].append(command)
                    timing = result.get("timing_ms", 0)
                    print(f"          ✓ Success ({timing}ms)")
                else:
                    pyskyq_verification["failed"].append(command)
                    error = result.get("error", "Unknown error")
                    print(f"          ✗ Failed: {error}")
                
                time.sleep(0.2)  # Longer delay for pyskyqremote
            
            success_rate = len(pyskyq_verification["working"]) / len(self.all_commands) * 100
            print(f"   pyskyqremote SUMMARY: {len(pyskyq_verification['working'])}/{len(self.all_commands)} commands working ({success_rate:.1f}%)")
            
        except ImportError:
            pyskyq_verification["error"] = "pyskyqremote library not installed"
            print("   pyskyqremote library not available, skipping library tests")
        except Exception as e:
            pyskyq_verification["error"] = str(e)
            print(f"   pyskyqremote testing failed: {e}")
        
        self.discovery_report["pyskyqremote_verification"] = pyskyq_verification
    
    def _test_tcp_command(self, command: str) -> Dict[str, Any]:
        """Test a command via direct TCP with timing."""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device_ip, self.remote_port))
            
            command_bytes = f"{command}\n".encode('utf-8')
            sock.send(command_bytes)
            
            sock.settimeout(3)
            response = sock.recv(256)
            total_time = time.time() - start_time
            
            sock.close()
            
            response_text = response.decode('utf-8', errors='ignore').strip()
            success = response_text.startswith("SKY") or len(response_text) > 0
            
            return {
                "success": success,
                "command": command,
                "timing_ms": int(total_time * 1000),
                "response_text": response_text,
                "response_length": len(response)
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _test_pyskyqremote_command(self, skyq_remote, command: str) -> Dict[str, Any]:
        """Test a command via pyskyqremote with timing."""
        try:
            start_time = time.time()
            result = skyq_remote.press(command)
            total_time = time.time() - start_time
            
            success = result if result is not None else True
            
            return {
                "success": success,
                "command": command,
                "timing_ms": int(total_time * 1000),
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _analyze_command_compatibility(self):
        """Analyze command compatibility between TCP and pyskyqremote."""
        tcp_results = self.discovery_report.get("tcp_command_verification", {})
        pyskyq_results = self.discovery_report.get("pyskyqremote_verification", {})
        
        compatibility_matrix = {
            "tcp_only": [],
            "pyskyqremote_only": [],
            "both_working": [],
            "both_failing": [],
            "command_analysis": {}
        }
        
        print("   Analyzing command compatibility...")
        
        tcp_working = set(tcp_results.get("working", []))
        tcp_failing = set(tcp_results.get("failed", []))
        pyskyq_working = set(pyskyq_results.get("working", []))
        pyskyq_failing = set(pyskyq_results.get("failed", []))
        
        for command in self.all_commands:
            tcp_works = command in tcp_working
            pyskyq_works = command in pyskyq_working
            
            if tcp_works and pyskyq_works:
                compatibility_matrix["both_working"].append(command)
                compatibility = "both"
            elif tcp_works and not pyskyq_works:
                compatibility_matrix["tcp_only"].append(command)
                compatibility = "tcp_only"
            elif not tcp_works and pyskyq_works:
                compatibility_matrix["pyskyqremote_only"].append(command)
                compatibility = "pyskyqremote_only"
            else:
                compatibility_matrix["both_failing"].append(command)
                compatibility = "none"
            
            compatibility_matrix["command_analysis"][command] = {
                "tcp_working": tcp_works,
                "pyskyqremote_working": pyskyq_works,
                "compatibility": compatibility,
                "recommended_method": "tcp" if tcp_works and not pyskyq_works else "pyskyqremote" if pyskyq_works else "none"
            }
        
        # Print summary
        print(f"      Both methods work: {len(compatibility_matrix['both_working'])} commands")
        print(f"      TCP only: {len(compatibility_matrix['tcp_only'])} commands")
        print(f"      pyskyqremote only: {len(compatibility_matrix['pyskyqremote_only'])} commands")
        print(f"      Neither works: {len(compatibility_matrix['both_failing'])} commands")
        
        if compatibility_matrix["tcp_only"]:
            print(f"      TCP-ONLY commands: {', '.join(compatibility_matrix['tcp_only'][:10])}{'...' if len(compatibility_matrix['tcp_only']) > 10 else ''}")
        
        self.discovery_report["command_compatibility_matrix"] = compatibility_matrix
    
    def _generate_integration_recommendations(self):
        """Generate specific integration recommendations."""
        compatibility = self.discovery_report.get("command_compatibility_matrix", {})
        tcp_results = self.discovery_report.get("tcp_command_verification", {})
        pyskyq_results = self.discovery_report.get("pyskyqremote_verification", {})
        
        recommendations = {
            "integration_strategy": {},
            "direct_tcp_commands": compatibility.get("tcp_only", []),
            "pyskyqremote_commands": compatibility.get("both_working", []),
            "unsupported_commands": compatibility.get("both_failing", []),
            "client_modifications_needed": [],
            "code_changes": {}
        }
        
        print("   Generating integration recommendations...")
        
        tcp_only_count = len(compatibility.get("tcp_only", []))
        both_working_count = len(compatibility.get("both_working", []))
        total_working = tcp_only_count + both_working_count
        
        # Integration strategy
        if tcp_only_count > 0:
            recommendations["integration_strategy"] = {
                "approach": "hybrid",
                "description": f"Use pyskyqremote for {both_working_count} commands, direct TCP for {tcp_only_count} commands",
                "total_working_commands": total_working,
                "success_rate": (total_working / len(self.all_commands)) * 100
            }
            
            recommendations["client_modifications_needed"] = [
                "Add command routing logic in send_remote_command()",
                "Maintain list of TCP-only commands",
                "Implement fallback to direct TCP for unsupported commands"
            ]
            
            # Generate specific code changes
            tcp_only_commands = compatibility.get("tcp_only", [])
            recommendations["code_changes"] = {
                "client.py": {
                    "add_tcp_command_list": tcp_only_commands,
                    "modify_send_remote_command": True,
                    "add_direct_tcp_method": True
                },
                "remote.py": {
                    "update_simple_commands": tcp_only_commands,
                    "add_new_ui_buttons": True
                }
            }
        else:
            recommendations["integration_strategy"] = {
                "approach": "pyskyqremote_only",
                "description": "All working commands supported by pyskyqremote",
                "total_working_commands": both_working_count,
                "success_rate": (both_working_count / len(self.all_commands)) * 100
            }
        
        # Device specific notes
        device_info = self.discovery_report.get("device_analysis", {}).get("device_info", {})
        if device_info.get("success"):
            model = device_info.get("model", "Unknown")
            recommendations["device_specific_notes"] = [
                f"Tested on {model}",
                f"TCP commands working: {len(tcp_results.get('working', []))}",
                f"pyskyqremote commands working: {len(pyskyq_results.get('working', []))}"
            ]
        
        print(f"      Strategy: {recommendations['integration_strategy']['approach']}")
        print(f"      Total working commands: {recommendations['integration_strategy']['total_working_commands']}")
        print(f"      Success rate: {recommendations['integration_strategy']['success_rate']:.1f}%")
        
        self.discovery_report["integration_recommendations"] = recommendations
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save discovery report with timestamp."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_model = self.discovery_report.get("device_analysis", {}).get("device_info", {}).get("model", "unknown")
            filename = f"skyq_discovery_enhanced_{device_model}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_report, f, indent=2, default=str)
            print(f"SUCCESS: Enhanced report saved to {filename}")
            return filename
        except Exception as e:
            print(f"ERROR: Failed to save report: {e}")
            try:
                fallback_name = f"skyq_discovery_backup_{int(time.time())}.json"
                with open(fallback_name, 'w', encoding='utf-8') as f:
                    json.dump(self.discovery_report, f, indent=2, default=str)
                print(f"SUCCESS: Report saved to fallback file {fallback_name}")
                return fallback_name
            except Exception as e2:
                print(f"CRITICAL: Could not save report at all: {e2}")
                return ""


def main():
    """Main function for enhanced discovery."""
    print("Enhanced SkyQ Discovery Script - TCP + pyskyqremote Testing")
    print("=" * 60)
    
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
    
    discovery = None
    report_file = ""
    
    try:
        # Run discovery
        discovery = EnhancedSkyQDiscovery(device_ip, rest_port, remote_port)
        print("Starting enhanced discovery process...")
        results = discovery.run_discovery()
        
        print("\nDiscovery completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nDiscovery cancelled by user")
        if discovery:
            print("Saving partial results...")
    except Exception as e:
        print(f"\n\nERROR during discovery: {e}")
        print("Attempting to save partial results...")
        traceback.print_exc()
    
    # ALWAYS try to save results
    if discovery and discovery.discovery_report:
        try:
            report_file = discovery.save_report()
        except Exception as e:
            print(f"Failed to save report: {e}")
    
    # Print summary
    try:
        print("\n" + "=" * 60)
        print("ENHANCED DISCOVERY RESULTS SUMMARY")
        print("=" * 60)
        
        if discovery and discovery.discovery_report:
            results = discovery.discovery_report
            
            # TCP results
            tcp_verification = results.get("tcp_command_verification", {})
            if tcp_verification:
                tcp_working = tcp_verification.get("working", [])
                print(f"Direct TCP Commands: {len(tcp_working)}/{tcp_verification.get('total_tested', 0)} working")
            
            # pyskyqremote results  
            pyskyq_verification = results.get("pyskyqremote_verification", {})
            if pyskyq_verification.get("library_available"):
                pyskyq_working = pyskyq_verification.get("working", [])
                print(f"pyskyqremote Commands: {len(pyskyq_working)}/{pyskyq_verification.get('total_tested', 0)} working")
            else:
                print("pyskyqremote: Not available or failed to connect")
            
            # Compatibility analysis
            compatibility = results.get("command_compatibility_matrix", {})
            if compatibility:
                tcp_only = compatibility.get("tcp_only", [])
                both_working = compatibility.get("both_working", [])
                
                print(f"\nCOMPATIBILITY ANALYSIS:")
                print(f"Both methods work: {len(both_working)} commands")
                print(f"TCP only: {len(tcp_only)} commands")
                
                if tcp_only:
                    print(f"TCP-ONLY COMMANDS (need direct TCP):")
                    for cmd in tcp_only:
                        print(f"  - {cmd}")
            
            # Integration recommendations
            recommendations = results.get("integration_recommendations", {})
            if recommendations:
                strategy = recommendations.get("integration_strategy", {})
                print(f"\nRECOMMENDED STRATEGY: {strategy.get('approach', 'unknown')}")
                print(f"Total working commands: {strategy.get('total_working_commands', 0)}")
                print(f"Success rate: {strategy.get('success_rate', 0):.1f}%")
            
            # Device info
            device_info = results.get("device_analysis", {}).get("device_info", {})
            if device_info.get("success"):
                print(f"Device: {device_info.get('model', 'Unknown')} ({device_info.get('serial', 'Unknown')})")
        
        if report_file:
            print(f"\nDETAILED REPORT SAVED: {report_file}")
            print("=" * 60)
            print("IMPORTANT: Send this JSON file to meir.miyara@gmail.com")
            print("Include your SkyQ device model and any specific issues")
            print("This enhanced report shows both TCP and pyskyqremote compatibility")
            print("=" * 60)
        
        print(f"\nUsage: python {sys.argv[0]} [IP_ADDRESS] [REST_PORT]")
        
    except Exception as e:
        print(f"Error printing summary: {e}")
    
    # Keep window open for user to see results
    try:
        input("\nPress ENTER to exit...")
    except:
        pass


if __name__ == "__main__":
    main()