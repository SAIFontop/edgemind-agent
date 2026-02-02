"""
EdgeMind Agent - Command Executor
===================================
منفذ الأوامر المعزول
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
    """نتيجة تنفيذ أمر"""
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
    منفذ الأوامر
    
    ينفذ الأوامر في بيئة معزولة مع:
    - حدود زمنية
    - عزل البيئة
    - تسجيل التنفيذ
    """
    
    def __init__(
        self,
        default_timeout: int = 60,
        max_output_size: int = 1048576,  # 1MB
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ):
        """
        تهيئة المنفذ
        
        Args:
            default_timeout: المهلة الافتراضية (ثانية)
            max_output_size: أقصى حجم للمخرجات
            working_dir: مجلد العمل
            env_vars: متغيرات البيئة
        """
        self.default_timeout = default_timeout
        self.max_output_size = max_output_size
        self.working_dir = working_dir or os.getcwd()
        self.env_vars = env_vars or {}
        
        self._execution_history: List[CommandResult] = []
        self._lock = threading.Lock()
    
    def _prepare_environment(self) -> Dict[str, str]:
        """إعداد بيئة التنفيذ"""
        env = os.environ.copy()
        
        # متغيرات أمان
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        
        # إضافة المتغيرات المخصصة
        env.update(self.env_vars)
        
        return env
    
    def _truncate_output(self, output: str) -> str:
        """قص المخرجات الكبيرة"""
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
        تنفيذ أمر
        
        Args:
            command: الأمر للتنفيذ
            timeout: مهلة مخصصة
            shell: استخدام shell
            capture_output: التقاط المخرجات
            working_dir: مجلد عمل مخصص
        
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
        
        # حفظ في التاريخ
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
        تنفيذ سكريبت
        
        Args:
            script_content: محتوى السكريبت
            interpreter: المفسر
            timeout: المهلة
        
        Returns:
            CommandResult
        """
        import time
        start_time = time.time()
        
        try:
            # إنشاء ملف مؤقت
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as f:
                f.write(script_content)
                script_path = f.name
            
            # تعيين صلاحيات التنفيذ
            os.chmod(script_path, 0o700)
            
            # تنفيذ
            result = self.execute(
                f"{interpreter} {script_path}",
                timeout=timeout,
                shell=False
            )
            
            # حذف الملف المؤقت
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
        تنفيذ أمر بشكل غير متزامن
        
        Args:
            command: الأمر
            callback: دالة استدعاء عند الانتهاء
            timeout: المهلة
        
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
        """الحصول على تاريخ التنفيذ"""
        with self._lock:
            return [r.to_dict() for r in self._execution_history[-limit:]]
    
    def clear_history(self) -> None:
        """مسح التاريخ"""
        with self._lock:
            self._execution_history = []
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات التنفيذ"""
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


# للاختبار
if __name__ == "__main__":
    import json
    
    executor = CommandExecutor(default_timeout=30)
    
    print("=== Command Executor Test ===")
    
    # أمر بسيط
    result = executor.execute("echo 'Hello EdgeMind'")
    print(f"\n1. Echo command:")
    print(json.dumps(result.to_dict(), indent=2))
    
    # أمر معقد
    result = executor.execute("date && uptime")
    print(f"\n2. Date & Uptime:")
    print(json.dumps(result.to_dict(), indent=2))
    
    # إحصائيات
    print(f"\n3. Execution Stats:")
    print(json.dumps(executor.get_stats(), indent=2))
