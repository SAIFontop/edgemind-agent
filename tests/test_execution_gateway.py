"""Tests for safe execution gateway."""

import pytest
from edgemind_agent.execution.gateway import SafeExecutionGateway
from edgemind_agent.security.policy import SecurityPolicy


class TestSafeExecutionGateway:
    """Test cases for SafeExecutionGateway class."""

    def test_initialization(self):
        """Test gateway initialization."""
        gateway = SafeExecutionGateway(dry_run=True)
        assert gateway.dry_run
        assert len(gateway.execution_history) == 0

    def test_dry_run_mode(self):
        """Test dry run mode."""
        gateway = SafeExecutionGateway(dry_run=True)
        policy = SecurityPolicy(strict_mode=True)
        
        validation = policy.validate_command('ls -la')
        result = gateway.execute_command('ls -la', validation)
        
        assert not result['executed']
        assert result['dry_run']
        assert result['exit_code'] == 0

    def test_blocked_command_execution(self):
        """Test that blocked commands are not executed."""
        gateway = SafeExecutionGateway(dry_run=False)
        
        # Create a validation result for a blocked command
        validation = {
            'allowed': False,
            'risk_level': 'FORBIDDEN',
            'reason': 'Command not allowed',
            'command': 'rm -rf /'
        }
        
        result = gateway.execute_command('rm -rf /', validation)
        
        assert not result['executed']
        assert result['blocked']
        assert result['exit_code'] == -1

    def test_successful_command_execution(self):
        """Test successful command execution."""
        gateway = SafeExecutionGateway(dry_run=False)
        policy = SecurityPolicy(strict_mode=True)
        
        validation = policy.validate_command('echo "test"')
        result = gateway.execute_command('echo "test"', validation, timeout=5)
        
        if result['executed']:
            assert result['exit_code'] == 0
            assert 'test' in result['stdout']
            assert result['success']

    def test_execution_history(self):
        """Test execution history tracking."""
        gateway = SafeExecutionGateway(dry_run=True)
        policy = SecurityPolicy(strict_mode=True)
        
        # Execute a few commands
        for cmd in ['ls', 'pwd', 'whoami']:
            validation = policy.validate_command(cmd)
            gateway.execute_command(cmd, validation)
        
        history = gateway.get_execution_history()
        assert len(history) == 3
        
        # Test limit
        limited_history = gateway.get_execution_history(limit=2)
        assert len(limited_history) == 2

    def test_clear_history(self):
        """Test clearing execution history."""
        gateway = SafeExecutionGateway(dry_run=True)
        policy = SecurityPolicy(strict_mode=True)
        
        validation = policy.validate_command('ls')
        gateway.execute_command('ls', validation)
        
        assert len(gateway.execution_history) == 1
        
        gateway.clear_history()
        assert len(gateway.execution_history) == 0

    def test_execution_statistics(self):
        """Test execution statistics."""
        gateway = SafeExecutionGateway(dry_run=False)
        policy = SecurityPolicy(strict_mode=True)
        
        # Execute some commands (using echo which should work)
        validation = policy.validate_command('echo "test"')
        gateway.execute_command('echo "test"', validation, timeout=5)
        
        # Block a command
        blocked_validation = {
            'allowed': False,
            'risk_level': 'FORBIDDEN',
            'command': 'rm -rf /'
        }
        gateway.execute_command('rm -rf /', blocked_validation)
        
        stats = gateway.get_statistics()
        assert stats['total_executions'] >= 2
        assert stats['blocked'] >= 1

    def test_invalid_plan_execution(self):
        """Test execution of invalid plan."""
        gateway = SafeExecutionGateway(dry_run=True)
        
        invalid_plan = {
            'valid': False,
            'reason': 'Test invalid plan'
        }
        
        result = gateway.execute_plan(invalid_plan, require_approval=False)
        
        assert not result['executed']
        assert 'Plan validation failed' in result['reason']

    def test_plan_requiring_approval(self):
        """Test plan execution that requires approval."""
        gateway = SafeExecutionGateway(dry_run=True)
        
        plan = {
            'valid': True,
            'requires_approval': True,
            'highest_risk': 'HIGH',
            'validated_steps': []
        }
        
        result = gateway.execute_plan(plan, require_approval=True)
        
        assert not result['executed']
        assert 'requires approval' in result['reason']
