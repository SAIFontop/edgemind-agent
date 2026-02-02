"""
EdgeMind Agent - Context Builder
=================================
جامع سياق النظام للتحليل الذكي
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
    """هيكل سياق النظام"""
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
        """تحويل إلى قاموس"""
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
    جامع سياق النظام
    
    يجمع معلومات من:
    - نظام التشغيل
    - العتاد
    - الشبكة
    - الخدمات
    - السجلات
    """
    
    def __init__(self, max_log_lines: int = 50):
        """
        تهيئة الجامع
        
        Args:
            max_log_lines: أقصى عدد أسطر من السجلات
        """
        self.max_log_lines = max_log_lines
        self._is_raspberry_pi = self._detect_raspberry_pi()
        self._cache: Optional[SystemContext] = None
        self._cache_time: Optional[datetime] = None
        self._cache_duration = 60  # ثانية
    
    def _detect_raspberry_pi(self) -> bool:
        """كشف إذا كان الجهاز Raspberry Pi"""
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
        تنفيذ أمر وإرجاع الناتج
        
        Args:
            command: الأمر
            timeout: مهلة التنفيذ
            shell: استخدام shell
        
        Returns:
            ناتج الأمر أو None
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
        """الحصول على اسم المضيف"""
        return platform.node() or "unknown"
    
    def get_os_info(self) -> Dict[str, str]:
        """الحصول على معلومات نظام التشغيل"""
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown"
        }
        
        # معلومات إضافية لـ Linux
        if platform.system() == "Linux":
            # قراءة /etc/os-release
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
        """الحصول على معلومات العتاد"""
        hardware = {}
        
        if psutil:
            # CPU
            hardware["cpu"] = {
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=0.1)
            }
        
        # معلومات Raspberry Pi خاصة
        if self._is_raspberry_pi:
            # درجة الحرارة
            temp = self._run_command("vcgencmd measure_temp")
            if temp:
                hardware["temperature"] = temp.replace("temp=", "")
            
            # حالة Throttling
            throttled = self._run_command("vcgencmd get_throttled")
            if throttled:
                hardware["throttled"] = throttled
            
            # معلومات الطراز
            model = self._run_command("cat /proc/device-tree/model")
            if model:
                hardware["model"] = model.replace("\x00", "")
        
        return hardware
    
    def get_memory_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الذاكرة"""
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
            # بديل باستخدام أوامر النظام
            free_output = self._run_command("free -m")
            if free_output:
                memory["raw"] = free_output
        
        return memory
    
    def get_disk_info(self) -> List[Dict[str, Any]]:
        """الحصول على معلومات الأقراص"""
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
            # بديل
            df_output = self._run_command("df -h")
            if df_output:
                disks.append({"raw": df_output})
        
        return disks
    
    def get_network_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الشبكة"""
        network = {"interfaces": []}
        
        if psutil:
            # واجهات الشبكة
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
            
            # إحصائيات الشبكة
            io = psutil.net_io_counters()
            network["stats"] = {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv
            }
        else:
            # بديل
            ip_output = self._run_command("ip addr")
            if ip_output:
                network["raw"] = ip_output
        
        return network
    
    def get_services_status(
        self, 
        services: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        الحصول على حالة الخدمات
        
        Args:
            services: قائمة الخدمات (أو None للخدمات الفاشلة فقط)
        
        Returns:
            قائمة حالات الخدمات
        """
        result = []
        
        if platform.system() != "Linux":
            return result
        
        if services:
            # خدمات محددة
            for service in services:
                status = self._run_command(
                    f"systemctl is-active {service} 2>/dev/null"
                )
                result.append({
                    "name": service,
                    "status": status or "unknown"
                })
        else:
            # الخدمات الفاشلة فقط
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
        الحصول على الأخطاء الأخيرة
        
        Args:
            log_files: ملفات السجل
        
        Returns:
            قائمة الأخطاء
        """
        errors = []
        
        if platform.system() != "Linux":
            return errors
        
        # journalctl للأخطاء
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
        بناء سياق النظام الكامل
        
        Args:
            include_services: خدمات محددة للفحص
            include_logs: تضمين السجلات
            custom_data: بيانات إضافية
            use_cache: استخدام الذاكرة المؤقتة
        
        Returns:
            SystemContext
        """
        # فحص الكاش
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
        
        # تحديث الكاش
        self._cache = context
        self._cache_time = datetime.now()
        
        return context
    
    def build_minimal(self) -> Dict[str, Any]:
        """بناء سياق مختصر (خفيف على الموارد)"""
        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": self.get_hostname(),
            "is_raspberry_pi": self._is_raspberry_pi,
            "memory_percent": psutil.virtual_memory().percent if psutil else None,
            "cpu_percent": psutil.cpu_percent(interval=0.1) if psutil else None,
            "disk_percent": psutil.disk_usage("/").percent if psutil else None
        }


# للاختبار المباشر
if __name__ == "__main__":
    import json
    
    builder = ContextBuilder()
    
    print("=== Minimal Context ===")
    minimal = builder.build_minimal()
    print(json.dumps(minimal, indent=2, ensure_ascii=False))
    
    print("\n=== Full Context ===")
    full = builder.build()
    print(json.dumps(full.to_dict(), indent=2, ensure_ascii=False))
