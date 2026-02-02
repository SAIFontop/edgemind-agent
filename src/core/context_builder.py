"""
EdgeMind Agent - Context Builder
=================================
System context collector for intelligent analysis
"""

import os
import subprocess
import platform
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class SystemContext:
    """System context structure"""
    timestamp: str
    hostname: str
    os_info: Dict[str, str]
    hardware: Dict[str, Any]
    memory: Dict[str, Any]
    disk: List[Dict[str, Any]]
    network: Dict[str, Any]
    services: List[Dict[str, str]]
    recent_errors: List[str]
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "os_info": self.os_info,
            "hardware": self.hardware,
            "memory": self.memory,
            "disk": self.disk,
            "network": self.network,
            "services": self.services,
            "recent_errors": self.recent_errors,
            "custom_data": self.custom_data
        }


class ContextBuilder:
    """
    System Context Collector
    
    Collects information from:
    - Operating system
    - Hardware
    - Network
    - Services
    - Logs
    """
    
    def __init__(self, max_log_lines: int = 50):
        """
        Initialize the collector
        
        Args:
            max_log_lines: Maximum number of log lines
        """
        self.max_log_lines = max_log_lines
        self._is_raspberry_pi = self._detect_raspberry_pi()
        self._cache: Optional[SystemContext] = None
        self._cache_time: Optional[datetime] = None
        self._cache_duration = 60  # seconds
    
    def _detect_raspberry_pi(self) -> bool:
        """Detect if device is Raspberry Pi"""
        try:
            with open("/proc/device-tree/model", "r") as f:
                model = f.read()
                return "raspberry" in model.lower()
        except:
            return False
    
    def _run_command(
        self, 
        command: str, 
        timeout: int = 10,
        shell: bool = True
    ) -> Optional[str]:
        """
        Execute command and return output
        
        Args:
            command: The command
            timeout: Execution timeout
            shell: Use shell
        
        Returns:
            Command output or None
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def get_hostname(self) -> str:
        """Get hostname"""
        return platform.node() or "unknown"
    
    def get_os_info(self) -> Dict[str, str]:
        """Get operating system information"""
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown"
        }
        
        # Additional info for Linux
        if platform.system() == "Linux":
            # Read /etc/os-release
            try:
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            info["distro"] = line.split("=")[1].strip().strip('"')
                            break
            except:
                pass
            
            # Kernel
            kernel = self._run_command("uname -r")
            if kernel:
                info["kernel"] = kernel
            
            # Uptime
            uptime = self._run_command("uptime -p")
            if uptime:
                info["uptime"] = uptime
        
        return info
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        hardware = {}
        
        if psutil:
            # CPU
            hardware["cpu"] = {
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=0.1)
            }
        
        # Raspberry Pi specific info
        if self._is_raspberry_pi:
            # Temperature
            temp = self._run_command("vcgencmd measure_temp")
            if temp:
                hardware["temperature"] = temp.replace("temp=", "")
            
            # Throttling status
            throttled = self._run_command("vcgencmd get_throttled")
            if throttled:
                hardware["throttled"] = throttled
            
            # Model info
            model = self._run_command("cat /proc/device-tree/model")
            if model:
                hardware["model"] = model.replace("\x00", "")
        
        return hardware
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        memory = {}
        
        if psutil:
            mem = psutil.virtual_memory()
            memory = {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "free_gb": round(mem.available / (1024**3), 2),
                "percent_used": mem.percent
            }
            
            # Swap
            swap = psutil.swap_memory()
            memory["swap"] = {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent_used": swap.percent
            }
        else:
            # Alternative using system commands
            free_output = self._run_command("free -m")
            if free_output:
                memory["raw"] = free_output
        
        return memory
    
    def get_disk_info(self) -> List[Dict[str, Any]]:
        """Get disk information"""
        disks = []
        
        if psutil:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": usage.percent
                    })
                except:
                    pass
        else:
            # Alternative
            df_output = self._run_command("df -h")
            if df_output:
                disks.append({"raw": df_output})
        
        return disks
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        network = {"interfaces": []}
        
        if psutil:
            # Network interfaces
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for iface, addresses in addrs.items():
                iface_info = {
                    "name": iface,
                    "is_up": stats.get(iface, None) and stats[iface].isup,
                    "addresses": []
                }
                
                for addr in addresses:
                    if addr.family.name == "AF_INET":
                        iface_info["addresses"].append({
                            "type": "IPv4",
                            "address": addr.address,
                            "netmask": addr.netmask
                        })
                    elif addr.family.name == "AF_INET6":
                        iface_info["addresses"].append({
                            "type": "IPv6",
                            "address": addr.address
                        })
                
                network["interfaces"].append(iface_info)
            
            # Network statistics
            io = psutil.net_io_counters()
            network["stats"] = {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv
            }
        else:
            # Alternative
            ip_output = self._run_command("ip addr")
            if ip_output:
                network["raw"] = ip_output
        
        return network
    
    def get_services_status(
        self, 
        services: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Get services status
        
        Args:
            services: List of services (or None for failed services only)
        
        Returns:
            List of service statuses
        """
        result = []
        
        if platform.system() != "Linux":
            return result
        
        if services:
            # Specific services
            for service in services:
                status = self._run_command(
                    f"systemctl is-active {service} 2>/dev/null"
                )
                result.append({
                    "name": service,
                    "status": status or "unknown"
                })
        else:
            # Failed services only
            failed = self._run_command(
                "systemctl --failed --no-legend --no-pager 2>/dev/null"
            )
            if failed:
                for line in failed.split("\n"):
                    if line.strip():
                        parts = line.split()
                        if parts:
                            result.append({
                                "name": parts[0],
                                "status": "failed"
                            })
        
        return result
    
    def get_recent_errors(
        self, 
        log_files: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get recent errors
        
        Args:
            log_files: Log files
        
        Returns:
            List of errors
        """
        errors = []
        
        if platform.system() != "Linux":
            return errors
        
        # journalctl for errors
        journal_errors = self._run_command(
            f"journalctl -p err -n {self.max_log_lines} --no-pager 2>/dev/null"
        )
        if journal_errors:
            for line in journal_errors.split("\n")[:self.max_log_lines]:
                if line.strip():
                    errors.append(line.strip())
        
        return errors
    
    def build(
        self,
        include_services: Optional[List[str]] = None,
        include_logs: bool = True,
        custom_data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> SystemContext:
        """
        Build full system context
        
        Args:
            include_services: Specific services to check
            include_logs: Include logs
            custom_data: Additional data
            use_cache: Use cache
        
        Returns:
            SystemContext
        """
        # Check cache
        if use_cache and self._cache:
            cache_age = (datetime.now() - self._cache_time).total_seconds()
            if cache_age < self._cache_duration:
                return self._cache
        
        context = SystemContext(
            timestamp=datetime.now().isoformat(),
            hostname=self.get_hostname(),
            os_info=self.get_os_info(),
            hardware=self.get_hardware_info(),
            memory=self.get_memory_info(),
            disk=self.get_disk_info(),
            network=self.get_network_info(),
            services=self.get_services_status(include_services),
            recent_errors=self.get_recent_errors() if include_logs else [],
            custom_data=custom_data or {}
        )
        
        # Update cache
        self._cache = context
        self._cache_time = datetime.now()
        
        return context
    
    def build_minimal(self) -> Dict[str, Any]:
        """Build minimal context (lightweight on resources)"""
        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": self.get_hostname(),
            "is_raspberry_pi": self._is_raspberry_pi,
            "memory_percent": psutil.virtual_memory().percent if psutil else None,
            "cpu_percent": psutil.cpu_percent(interval=0.1) if psutil else None,
            "disk_percent": psutil.disk_usage("/").percent if psutil else None
        }


# For direct testing
if __name__ == "__main__":
    import json
    
    builder = ContextBuilder()
    
    print("=== Minimal Context ===")
    minimal = builder.build_minimal()
    print(json.dumps(minimal, indent=2, ensure_ascii=False))
    
    print("\n=== Full Context ===")
    full = builder.build()
    print(json.dumps(full.to_dict(), indent=2, ensure_ascii=False))
