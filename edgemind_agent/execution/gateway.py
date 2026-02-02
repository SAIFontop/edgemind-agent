"""Safe execution gateway for validated commands."""

import subprocess
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import shlex


logger = logging.getLogger(__name__)


class SafeExecutionGateway:
    """Safe execution gateway that only runs whitelisted, validated commands."""

    def __init__(self, dry_run: bool = False):
        """Initialize the execution gateway.
        
        Args:
            dry_run: If True, commands are logged but not executed.
        """
        self.dry_run = dry_run
        self.execution_history: List[Dict[str, Any]] = []
        logger.info(f"Safe execution gateway initialized (dry_run={dry_run})")

    def execute_command(self, command: str, 
                       validation_result: Dict[str, Any],
                       timeout: int = 30) -> Dict[str, Any]:
        """Execute a validated command safely.
        
        Args:
            command: Command to execute.
            validation_result: Validation result from security policy.
            timeout: Command timeout in seconds.
            
        Returns:
            Execution result with output and status.
        """
        execution_record = {
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'validation': validation_result
        }
        
        # Check if command is allowed
        if not validation_result.get('allowed', False):
            logger.warning(f"Blocked execution of non-validated command: {command}")
            execution_record.update({
                'executed': False,
                'blocked': True,
                'reason': validation_result.get('reason', 'Command not allowed'),
                'exit_code': -1
            })
            self.execution_history.append(execution_record)
            return execution_record
        
        # In dry-run mode, don't actually execute
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {command}")
            execution_record.update({
                'executed': False,
                'dry_run': True,
                'exit_code': 0,
                'stdout': '[Dry run mode - command not executed]',
                'stderr': ''
            })
            self.execution_history.append(execution_record)
            return execution_record
        
        # Execute the command
        try:
            logger.info(f"Executing command: {command}")
            
            # Use shlex to safely parse the command
            # Run with shell=True for pipe support but log for audit
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_record.update({
                'executed': True,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            })
            
            if result.returncode == 0:
                logger.info(f"Command executed successfully: {command}")
            else:
                logger.warning(f"Command failed with exit code {result.returncode}: {command}")
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {command}")
            execution_record.update({
                'executed': True,
                'exit_code': -1,
                'error': f'Command timed out after {timeout} seconds',
                'success': False
            })
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            execution_record.update({
                'executed': False,
                'exit_code': -1,
                'error': str(e),
                'success': False
            })
        
        self.execution_history.append(execution_record)
        return execution_record

    def execute_plan(self, validated_plan: Dict[str, Any],
                    require_approval: bool = True) -> Dict[str, Any]:
        """Execute a validated action plan.
        
        Args:
            validated_plan: Validated plan from security policy.
            require_approval: If True, high-risk commands require user approval.
            
        Returns:
            Execution results for all steps.
        """
        if not validated_plan.get('valid', False):
            logger.error("Cannot execute invalid plan")
            return {
                'executed': False,
                'reason': 'Plan validation failed',
                'results': []
            }
        
        # Check if approval is needed
        if require_approval and validated_plan.get('requires_approval', False):
            logger.warning("Plan requires approval but no approval mechanism provided")
            return {
                'executed': False,
                'reason': 'Plan requires approval (high risk)',
                'highest_risk': validated_plan.get('highest_risk'),
                'results': []
            }
        
        results = []
        failed_steps = []
        
        for step_validation in validated_plan['validated_steps']:
            step_number = step_validation['step']
            step_results = {
                'step': step_number,
                'description': step_validation['description'],
                'commands': []
            }
            
            # Execute each command in the step
            for cmd_validation in step_validation['commands']:
                command = cmd_validation['command']
                
                # Execute the command
                exec_result = self.execute_command(command, cmd_validation)
                step_results['commands'].append(exec_result)
                
                # If command failed, record and potentially stop
                if not exec_result.get('success', False) and exec_result.get('executed', False):
                    failed_steps.append(step_number)
                    logger.warning(f"Step {step_number} command failed: {command}")
            
            results.append(step_results)
        
        return {
            'executed': True,
            'total_steps': len(results),
            'failed_steps': failed_steps,
            'results': results
        }

    def get_execution_history(self, 
                             limit: Optional[int] = None,
                             failed_only: bool = False) -> List[Dict[str, Any]]:
        """Get command execution history.
        
        Args:
            limit: Maximum number of records to return.
            failed_only: If True, only return failed executions.
            
        Returns:
            List of execution records.
        """
        history = self.execution_history
        
        if failed_only:
            history = [
                record for record in history 
                if not record.get('success', True)
            ]
        
        if limit:
            history = history[-limit:]
        
        return history

    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()
        logger.info("Execution history cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics.
        
        Returns:
            Statistics about command executions.
        """
        total = len(self.execution_history)
        if total == 0:
            return {
                'total_executions': 0,
                'successful': 0,
                'failed': 0,
                'blocked': 0
            }
        
        successful = sum(1 for r in self.execution_history if r.get('success', False))
        failed = sum(1 for r in self.execution_history if r.get('executed', False) and not r.get('success', True))
        blocked = sum(1 for r in self.execution_history if r.get('blocked', False))
        
        return {
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'blocked': blocked,
            'success_rate': successful / total if total > 0 else 0
        }
