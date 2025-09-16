#!/usr/bin/env python3
"""
SkyQ Discovery Script

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
    """Enhanced discovery with real device testing focus."""
    
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
            "integration_version": "1.0.14",
            "device_analysis": {},
            "command_verification": {},
            "timing_analysis": {},
            "command_discovery": {},
            "integration_recommendations": {},
            "errors": []
        }
        
        # Current working commands from integration
        self.current_commands = [
            "power", "standby", "on", "off", "up", "down", "left", "right", 
            "select", "back", "home", "menu", "play", "pause", "stop", 
            "record", "fastforward", "rewind", "channelup", "guide", "info",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "red", "green", "yellow", "blue", "volumeup", "volumedown", "mute",
            "sky", "search", "text", "help", "services"
        ]
        
        # Additional commands to test (including problematic ones)
        self.additional_commands = [
            "channeldown", "tvguide", "i", "boxoffice", "dismiss", "backup",
            "tv", "radio", "interactive", "mysky", "planner", "top", 
            "subtitle", "audio", "announce", "dismiss", "last", "list"
        ]
        
        # Known problematic commands from logs
        self.problematic_commands = ["channeldown", "tvguide", "i", "boxoffice", "dismiss", "backup"]
        
    def run_discovery(self) -> Dict[str, Any]:
        """Run comprehensive discovery with timing analysis."""
        print("Enhanced SkyQ Discovery - Production Ready")
        print("=" * 50)
        print(f"Target Device: {self.device_ip}:{self.rest_port}")
        print(f"Remote Port: {self.remote_port}")
        print(f"Integration Commands: {len(self.current_commands)}")
        print(f"Additional Tests: {len(self.additional_commands)}")
        print()
        
        try:
            # Phase 1: Device Analysis
            print("Phase 1: Device Information Analysis")
            self._analyze_device_info()
            
            # Phase 2: Current Command Verification with Timing
            print("\nPhase 2: Current Integration Command Verification")
            self._verify_current_commands()
            
            # Phase 3: Problematic Command Analysis
            print("\nPhase 3: Problematic Command Deep Analysis")
            self._analyze_problematic_commands()
            
            # Phase 4: Additional Command Discovery
            print("\nPhase 4: Additional Command Discovery")
            self._discover_additional_commands()
            
            # Phase 5: Timing Pattern Analysis
            print("\nPhase 5: Command Timing Analysis")
            self._analyze_timing_patterns()
            
            # Phase 6: Integration Recommendations
            print("\nPhase 6: Generate Integration Recommendations")
            self._generate_recommendations()
            
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
            "pyskyqremote_compatibility": {}
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
    
    def _verify_current_commands(self):
        """Verify current integration commands with detailed timing."""
        verification = {
            "total_tested": len(self.current_commands),
            "working": [],
            "failed": [],
            "timing_stats": {},
            "command_details": {}
        }
        
        print(f"   Testing {len(self.current_commands)} current integration commands...")
        
        for i, command in enumerate(self.current_commands):
            print(f"      [{i+1:2d}/{len(self.current_commands)}] Testing: {command}")
            
            result = self._test_command_with_timing(command)
            verification["command_details"][command] = result
            
            if result["success"]:
                verification["working"].append(command)
                timing = result.get("timing_ms", 0)
                print(f"          ✓ Success ({timing}ms)")
            else:
                verification["failed"].append(command)
                error = result.get("error", "Unknown error")
                print(f"          ✗ Failed: {error}")
            
            # Small delay between commands to avoid overwhelming device
            time.sleep(0.1)
        
        # Calculate timing statistics
        timings = [details.get("timing_ms", 0) for details in verification["command_details"].values() 
                  if details.get("success")]
        
        if timings:
            verification["timing_stats"] = {
                "min_ms": min(timings),
                "max_ms": max(timings),
                "avg_ms": int(sum(timings) / len(timings)),
                "median_ms": sorted(timings)[len(timings)//2]
            }
        
        success_rate = len(verification["working"]) / len(self.current_commands) * 100
        print(f"   SUMMARY: {len(verification['working'])}/{len(self.current_commands)} commands working ({success_rate:.1f}%)")
        
        self.discovery_report["command_verification"] = verification
    
    def _analyze_problematic_commands(self):
        """Deep analysis of known problematic commands."""
        analysis = {
            "commands_tested": [],
            "retry_results": {},
            "timing_variations": {},
            "error_patterns": {}
        }
        
        print(f"   Deep testing {len(self.problematic_commands)} problematic commands...")
        
        for command in self.problematic_commands:
            print(f"      Analyzing: {command}")
            analysis["commands_tested"].append(command)
            
            # Test multiple times with different timing
            retry_results = []
            timing_variations = []
            
            for attempt in range(3):
                print(f"        Attempt {attempt + 1}/3...")
                result = self._test_command_with_timing(command, delay_before=0.2 * attempt)
                retry_results.append(result)
                
                if result.get("timing_ms"):
                    timing_variations.append(result["timing_ms"])
                
                time.sleep(0.3)  # Longer delay between retries
            
            analysis["retry_results"][command] = retry_results
            analysis["timing_variations"][command] = timing_variations
            
            # Analyze error patterns
            errors = [r.get("error", "") for r in retry_results if not r.get("success")]
            if errors:
                analysis["error_patterns"][command] = {
                    "error_count": len(errors),
                    "unique_errors": list(set(errors)),
                    "consistent_failure": len(set(errors)) == 1
                }
        
        self.discovery_report["problematic_analysis"] = analysis
    
    def _discover_additional_commands(self):
        """Discover additional working commands."""
        discovery = {
            "commands_tested": len(self.additional_commands),
            "new_working": [],
            "still_failing": [],
            "command_details": {}
        }
        
        print(f"   Testing {len(self.additional_commands)} additional commands...")
        
        for i, command in enumerate(self.additional_commands):
            if command not in self.current_commands:  # Don't retest current commands
                print(f"      [{i+1:2d}/{len(self.additional_commands)}] Testing: {command}")
                
                result = self._test_command_with_timing(command)
                discovery["command_details"][command] = result
                
                if result["success"]:
                    discovery["new_working"].append(command)
                    timing = result.get("timing_ms", 0)
                    print(f"          ✓ NEW WORKING COMMAND ({timing}ms)")
                else:
                    discovery["still_failing"].append(command)
                    error = result.get("error", "Unknown error")
                    print(f"          ✗ Failed: {error}")
                
                time.sleep(0.1)
        
        print(f"   DISCOVERY: {len(discovery['new_working'])} new working commands found")
        if discovery["new_working"]:
            print(f"   NEW COMMANDS: {', '.join(discovery['new_working'])}")
        
        self.discovery_report["command_discovery"] = discovery
    
    def _test_command_with_timing(self, command: str, delay_before: float = 0) -> Dict[str, Any]:
        """Test a command with precise timing measurement."""
        if delay_before > 0:
            time.sleep(delay_before)
        
        try:
            # Connect
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.device_ip, self.remote_port))
            connect_time = time.time() - start_time
            
            # Send command
            command_start = time.time()
            command_bytes = f"{command}\n".encode('utf-8')
            sock.send(command_bytes)
            
            # Receive response
            sock.settimeout(3)
            response = sock.recv(256)
            total_time = time.time() - start_time
            
            sock.close()
            
            response_text = response.decode('utf-8', errors='ignore').strip()
            
            # Analyze response to determine success
            success = self._analyze_response_success(response_text, command)
            
            return {
                "success": success,
                "command": command,
                "timing_ms": int(total_time * 1000),
                "connect_time_ms": int(connect_time * 1000),
                "response_text": response_text,
                "response_length": len(response),
                "response_hex": response.hex() if response else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _analyze_response_success(self, response: str, command: str) -> bool:
        """Analyze response to determine if command was successful."""
        if not response:
            return False
        
        # SkyQ typically responds with "SKY" followed by version info for successful commands
        if response.startswith("SKY"):
            return True
        
        # Some commands might have different response patterns
        if len(response) > 0 and not any(error in response.lower() for error in ["error", "invalid", "fail"]):
            return True
        
        return False
    
    def _analyze_timing_patterns(self):
        """Analyze timing patterns across all commands."""
        timing_analysis = {
            "command_timing_distribution": {},
            "performance_categories": {},
            "outliers": {},
            "recommendations": []
        }
        
        print("   Analyzing command timing patterns...")
        
        # Collect all timing data
        all_timings = {}
        verification = self.discovery_report.get("command_verification", {})
        discovery = self.discovery_report.get("command_discovery", {})
        
        for command, details in verification.get("command_details", {}).items():
            if details.get("success") and details.get("timing_ms"):
                all_timings[command] = details["timing_ms"]
        
        for command, details in discovery.get("command_details", {}).items():
            if details.get("success") and details.get("timing_ms"):
                all_timings[command] = details["timing_ms"]
        
        if all_timings:
            timings = list(all_timings.values())
            avg_timing = sum(timings) / len(timings)
            
            # Categorize commands by performance
            fast_commands = [cmd for cmd, timing in all_timings.items() if timing < avg_timing * 0.8]
            normal_commands = [cmd for cmd, timing in all_timings.items() if avg_timing * 0.8 <= timing <= avg_timing * 1.2]
            slow_commands = [cmd for cmd, timing in all_timings.items() if timing > avg_timing * 1.2]
            
            timing_analysis["performance_categories"] = {
                "fast": {"commands": fast_commands, "count": len(fast_commands)},
                "normal": {"commands": normal_commands, "count": len(normal_commands)},
                "slow": {"commands": slow_commands, "count": len(slow_commands)}
            }
            
            # Identify outliers (commands taking >2x average time)
            outliers = [cmd for cmd, timing in all_timings.items() if timing > avg_timing * 2]
            timing_analysis["outliers"] = {
                "commands": outliers,
                "count": len(outliers)
            }
            
            print(f"      Average response time: {int(avg_timing)}ms")
            print(f"      Fast commands: {len(fast_commands)}")
            print(f"      Slow commands: {len(slow_commands)}")
            if outliers:
                print(f"      Timing outliers: {', '.join(outliers)}")
        
        self.discovery_report["timing_analysis"] = timing_analysis
    
    def _generate_recommendations(self):
        """Generate recommendations for integration improvements."""
        recommendations = {
            "summary": {},
            "add_commands": [],
            "remove_commands": [],
            "timing_optimizations": [],
            "device_specific_notes": []
        }
        
        verification = self.discovery_report.get("command_verification", {})
        discovery = self.discovery_report.get("command_discovery", {})
        device_info = self.discovery_report.get("device_analysis", {}).get("device_info", {})
        
        # Summary
        total_working = len(verification.get("working", [])) + len(discovery.get("new_working", []))
        total_tested = verification.get("total_tested", 0) + discovery.get("commands_tested", 0)
        
        recommendations["summary"] = {
            "total_working_commands": total_working,
            "total_tested_commands": total_tested,
            "success_rate": (total_working / total_tested * 100) if total_tested > 0 else 0,
            "integration_ready": total_working >= 40  # Threshold for good integration
        }
        
        # Commands to add
        new_working = discovery.get("new_working", [])
        if new_working:
            recommendations["add_commands"] = new_working
        
        # Commands to remove
        failed_commands = verification.get("failed", [])
        if failed_commands:
            recommendations["remove_commands"] = failed_commands
        
        # Device-specific notes
        if device_info.get("success"):
            model = device_info.get("model", "Unknown")
            recommendations["device_specific_notes"].append(f"Tested on {model}")
            
        # Special case for channeldown
        problematic = self.discovery_report.get("problematic_analysis", {})
        if "channeldown" in problematic.get("retry_results", {}):
            channeldown_results = problematic["retry_results"]["channeldown"]
            success_count = sum(1 for r in channeldown_results if r.get("success"))
            if success_count == 0:
                recommendations["device_specific_notes"].append(
                    "channeldown command consistently fails - may be device-specific limitation"
                )
            elif success_count < len(channeldown_results):
                recommendations["device_specific_notes"].append(
                    "channeldown command unreliable - consider excluding for stability"
                )
        
        print("   RECOMMENDATIONS:")
        if new_working:
            print(f"      ADD: {', '.join(new_working)}")
        if failed_commands:
            print(f"      REMOVE: {', '.join(failed_commands)}")
        print(f"      SUCCESS RATE: {recommendations['summary']['success_rate']:.1f}%")
        
        self.discovery_report["integration_recommendations"] = recommendations
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save discovery report with timestamp."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_model = self.discovery_report.get("device_analysis", {}).get("device_info", {}).get("model", "unknown")
            filename = f"skyq_discovery_{device_model}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_report, f, indent=2, default=str)
            print(f"SUCCESS: Report saved to {filename}")
            return filename
        except Exception as e:
            print(f"ERROR: Failed to save report: {e}")
            # Try to save with basic filename as fallback
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
    print("Enhanced SkyQ Discovery Script")
    print("=" * 40)
    
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
        print("Starting discovery process...")
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
    
    # ALWAYS try to save results, even if discovery failed
    if discovery and discovery.discovery_report:
        try:
            report_file = discovery.save_report()
        except Exception as e:
            print(f"Failed to save report: {e}")
    
    # Print summary regardless of completion status
    try:
        print("\n" + "=" * 50)
        print("DISCOVERY RESULTS SUMMARY")
        print("=" * 50)
        
        if discovery and discovery.discovery_report:
            results = discovery.discovery_report
            
            # Print current command results
            verification = results.get("command_verification", {})
            if verification:
                working = verification.get("working", [])
                failed = verification.get("failed", [])
                print(f"Current Integration Commands: {len(working)}/{verification.get('total_tested', 0)} working")
                if failed:
                    print(f"Failed commands: {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")
            
            # Print new discoveries
            discovery_results = results.get("command_discovery", {})
            if discovery_results:
                new_working = discovery_results.get("new_working", [])
                if new_working:
                    print(f"NEW WORKING COMMANDS FOUND: {len(new_working)}")
                    print(f"Commands: {', '.join(new_working)}")
                    print("\nTO ADD TO INTEGRATION:")
                    for cmd in new_working:
                        print(f"  - {cmd}")
            
            # Print device info
            device_info = results.get("device_analysis", {}).get("device_info", {})
            if device_info.get("success"):
                print(f"Device: {device_info.get('model', 'Unknown')} ({device_info.get('serial', 'Unknown')})")
            
            # Print recommendations
            recommendations = results.get("integration_recommendations", {})
            if recommendations:
                summary = recommendations.get("summary", {})
                print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
                print(f"Integration Ready: {'Yes' if summary.get('integration_ready') else 'No'}")
        
        if report_file:
            print(f"\nDETAILED REPORT SAVED: {report_file}")
            print("=" * 50)
            print("IMPORTANT: Send this JSON file to meir.miyara@gmail.com")
            print("Include device model and any issues encountered")
            print("=" * 50)
        else:
            print("\nWARNING: Could not save detailed report")
        
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
