"""
EdgeMind Agent - Command Executor
===================================
Isolated command executor
"""

import os
import subprocess
import shlex
import tempfile
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import threading
import queue


@dataclass
class CommandResult:
    """Command execution result"""
    command: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    timed_out: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "execution_time": self.execution_time,
            "timed_out": self.timed_out,
            "success": self.return_code == 0
        }


class CommandExecutor:
    """
    Command Executor
    
    Executes commands in isolated environment with:
    - Time limits
    - Environment isolation
    - Execution logging
    """
    
    def __init__(
        self,
        default_timeout: int = 60,
        max_output_size: int = 1048576,  # 1MB
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the executor
        
        Args:
            default_timeout: Default timeout (seconds)
            max_output_size: Maximum output size
            working_dir: Working directory
            env_vars: Environment variables
        """
        self.default_timeout = default_timeout
        self.max_output_size = max_output_size
        self.working_dir = working_dir or os.getcwd()
        self.env_vars = env_vars or {}
        
        self._execution_history: List[CommandResult] = []
        self._lock = threading.Lock()
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Setup execution environment"""
        env = os.environ.copy()
        
        # Security variables
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        
        # Add custom variables
        env.update(self.env_vars)
        
        return env
    
    def _truncate_output(self, output: str) -> str:
        """Truncate large output"""
        if len(output) > self.max_output_size:
            return output[:self.max_output_size] + "\n\n... [OUTPUT TRUNCATED]"
        return output
    
    def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        shell: bool = True,
        capture_output: bool = True,
        working_dir: Optional[str] = None
    ) -> CommandResult:
        """
        Execute command
        
        Args:
            command: Command to execute
            timeout: Custom timeout
            shell: Use shell
            capture_output: Capture output
            working_dir: Custom working directory
        
        Returns:
            CommandResult
        """
        import time
        start_time = time.time()
        
        try:
            env = self._prepare_environment()
            cwd = working_dir or self.working_dir
            
            process = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout or self.default_timeout,
                env=env,
                cwd=cwd
            )
            
            execution_time = time.time() - start_time
            
            result = CommandResult(
                command=command,
                stdout=self._truncate_output(process.stdout or ""),
                stderr=self._truncate_output(process.stderr or ""),
                return_code=process.returncode,
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            result = CommandResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {timeout or self.default_timeout} seconds",
                return_code=-1,
                execution_time=execution_time,
                timed_out=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = CommandResult(
                command=command,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=execution_time
            )
        
        # Save to history
        with self._lock:
            self._execution_history.append(result)
        
        return result
    
    def execute_script(
        self,
        script_content: str,
        interpreter: str = "/bin/bash",
        timeout: Optional[int] = None
    ) -> CommandResult:
        """
        Execute script
        
        Args:
            script_content: Script content
            interpreter: Interpreter
            timeout: Timeout
        
        Returns:
            CommandResult
        """
        import time
        start_time = time.time()
        
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as f:
                f.write(script_content)
                script_path = f.name
            
            # Set execute permissions
            os.chmod(script_path, 0o700)
            
            # Execute
            result = self.execute(
                f"{interpreter} {script_path}",
                timeout=timeout,
                shell=False
            )
            
            # Delete temp file
            os.unlink(script_path)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                command=f"[SCRIPT: {len(script_content)} chars]",
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=execution_time
            )
    
    def execute_async(
        self,
        command: str,
        callback=None,
        timeout: Optional[int] = None
    ) -> threading.Thread:
        """
        Execute command asynchronously
        
        Args:
            command: Command
            callback: Callback function on completion
            timeout: Timeout
        
        Returns:
            Thread
        """
        def run():
            result = self.execute(command, timeout=timeout)
            if callback:
                callback(result)
        
        thread = threading.Thread(target=run)
        thread.start()
        return thread
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history"""
        with self._lock:
            return [r.to_dict() for r in self._execution_history[-limit:]]
    
    def clear_history(self) -> None:
        """Clear history"""
        with self._lock:
            self._execution_history = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Execution statistics"""
        with self._lock:
            total = len(self._execution_history)
            successful = sum(1 for r in self._execution_history if r.return_code == 0)
            timed_out = sum(1 for r in self._execution_history if r.timed_out)
            
            avg_time = 0
            if total > 0:
                avg_time = sum(r.execution_time for r in self._execution_history) / total
            
            return {
                "total_executions": total,
                "successful": successful,
                "failed": total - successful,
                "timed_out": timed_out,
                "average_execution_time": round(avg_time, 3),
                "success_rate": round(successful / total * 100, 2) if total > 0 else 0
            }


# For testing
if __name__ == "__main__":
    import json
    
    executor = CommandExecutor(default_timeout=30)
    
    print("=== Command Executor Test ===")
    
    # Simple command
    result = executor.execute("echo 'Hello EdgeMind'")
    print(f"\n1. Echo command:")
    print(json.dumps(result.to_dict(), indent=2))
    
    # Complex command
    result = executor.execute("date && uptime")
    print(f"\n2. Date & Uptime:")
    print(json.dumps(result.to_dict(), indent=2))
    
    # Statistics
    print(f"\n3. Execution Stats:")
    print(json.dumps(executor.get_stats(), indent=2))
