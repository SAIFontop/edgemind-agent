"""Context collector module for gathering system state information."""

import os
import platform
import subprocess
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


logger = logging.getLogger(__name__)


class SystemContextCollector:
    """Collects system state, logs, and service status."""

    def __init__(self):
        """Initialize the context collector."""
        self.context = {}

    def collect_system_state(self) -> Dict[str, Any]:
        """Collect basic system state information.
        
        Returns:
            Dictionary containing system state information.
        """
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
            }
            
            # Get uptime (Linux/Unix)
            if platform.system() in ['Linux', 'Darwin']:
                try:
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.readline().split()[0])
                        state['uptime_seconds'] = uptime_seconds
                except (FileNotFoundError, IndexError, ValueError):
                    pass
            
            # Get memory info (Linux)
            if platform.system() == 'Linux':
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = {}
                        for line in f:
                            parts = line.split(':')
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip()
                                meminfo[key] = value
                        state['memory_info'] = meminfo
                except FileNotFoundError:
                    pass
            
            # Get CPU info
            if platform.system() == 'Linux':
                try:
                    with open('/proc/loadavg', 'r') as f:
                        loadavg = f.read().strip().split()[:3]
                        state['load_average'] = {
                            '1min': loadavg[0],
                            '5min': loadavg[1],
                            '15min': loadavg[2]
                        }
                except (FileNotFoundError, IndexError):
                    pass
            
            logger.info("System state collected successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error collecting system state: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def collect_logs(self, log_sources: Optional[List[str]] = None, 
                     max_lines: int = 100) -> Dict[str, List[str]]:
        """Collect recent log entries from system logs.
        
        Args:
            log_sources: List of log file paths to collect from.
            max_lines: Maximum number of lines to collect from each log.
            
        Returns:
            Dictionary mapping log sources to log entries.
        """
        if log_sources is None:
            log_sources = [
                '/var/log/syslog',
                '/var/log/messages',
                '/var/log/kern.log'
            ]
        
        logs = {}
        for log_source in log_sources:
            try:
                if os.path.exists(log_source) and os.access(log_source, os.R_OK):
                    with open(log_source, 'r') as f:
                        lines = f.readlines()
                        logs[log_source] = lines[-max_lines:]
                else:
                    logger.debug(f"Log source not accessible: {log_source}")
            except Exception as e:
                logger.error(f"Error reading log {log_source}: {e}")
                logs[log_source] = [f"Error: {str(e)}"]
        
        logger.info(f"Collected logs from {len(logs)} sources")
        return logs

    def collect_service_status(self, services: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Collect status of system services.
        
        Args:
            services: List of service names to check. If None, checks common services.
            
        Returns:
            Dictionary mapping service names to their status information.
        """
        if services is None:
            services = ['ssh', 'networking', 'cron', 'rsyslog']
        
        status_info = {}
        
        for service in services:
            try:
                # Try systemctl first (systemd)
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                status_info[service] = {
                    'active': result.stdout.strip() == 'active',
                    'status': result.stdout.strip(),
                    'method': 'systemctl'
                }
                
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Fallback to service command
                try:
                    result = subprocess.run(
                        ['service', service, 'status'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    status_info[service] = {
                        'active': result.returncode == 0,
                        'status': 'active' if result.returncode == 0 else 'inactive',
                        'method': 'service',
                        'output': result.stdout[:200]  # First 200 chars
                    }
                except Exception as e:
                    logger.error(f"Error checking service {service}: {e}")
                    status_info[service] = {
                        'active': False,
                        'status': 'unknown',
                        'error': str(e)
                    }
        
        logger.info(f"Collected status for {len(status_info)} services")
        return status_info

    def collect_command_errors(self, command_history: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Collect information about recent command errors.
        
        Args:
            command_history: List of command execution records with errors.
            
        Returns:
            List of command error records.
        """
        if command_history is None:
            return []
        
        errors = []
        for record in command_history:
            if record.get('exit_code', 0) != 0 or record.get('error'):
                errors.append({
                    'command': record.get('command', 'unknown'),
                    'exit_code': record.get('exit_code', -1),
                    'error': record.get('error', ''),
                    'stderr': record.get('stderr', ''),
                    'timestamp': record.get('timestamp', datetime.now().isoformat())
                })
        
        logger.info(f"Collected {len(errors)} command errors")
        return errors

    def collect_all(self, 
                    log_sources: Optional[List[str]] = None,
                    services: Optional[List[str]] = None,
                    command_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Collect all context information.
        
        Args:
            log_sources: Optional list of log files to collect.
            services: Optional list of services to check.
            command_history: Optional command execution history.
            
        Returns:
            Complete context dictionary.
        """
        context = {
            'collection_timestamp': datetime.now().isoformat(),
            'system_state': self.collect_system_state(),
            'logs': self.collect_logs(log_sources),
            'service_status': self.collect_service_status(services),
            'command_errors': self.collect_command_errors(command_history)
        }
        
        self.context = context
        logger.info("Complete context collected")
        return context

    def get_context_summary(self) -> str:
        """Get a human-readable summary of the collected context.
        
        Returns:
            String summary of the context.
        """
        if not self.context:
            return "No context collected yet."
        
        summary_parts = []
        
        # System state summary
        if 'system_state' in self.context:
            state = self.context['system_state']
            summary_parts.append(f"System: {state.get('platform', 'Unknown')} {state.get('platform_release', '')}")
            summary_parts.append(f"Hostname: {state.get('hostname', 'Unknown')}")
            if 'load_average' in state:
                la = state['load_average']
                summary_parts.append(f"Load Average: {la.get('1min', 'N/A')}, {la.get('5min', 'N/A')}, {la.get('15min', 'N/A')}")
        
        # Service status summary
        if 'service_status' in self.context:
            services = self.context['service_status']
            active_count = sum(1 for s in services.values() if s.get('active', False))
            summary_parts.append(f"Services: {active_count}/{len(services)} active")
        
        # Logs summary
        if 'logs' in self.context:
            logs = self.context['logs']
            total_lines = sum(len(lines) for lines in logs.values())
            summary_parts.append(f"Logs: {len(logs)} sources, {total_lines} lines")
        
        # Errors summary
        if 'command_errors' in self.context:
            errors = self.context['command_errors']
            summary_parts.append(f"Command Errors: {len(errors)}")
        
        return " | ".join(summary_parts)
