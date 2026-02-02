"""Tests for context collector module."""

import pytest
from edgemind_agent.context.collector import SystemContextCollector


class TestSystemContextCollector:
    """Test cases for SystemContextCollector class."""

    def test_initialization(self):
        """Test collector initialization."""
        collector = SystemContextCollector()
        assert collector.context == {}

    def test_collect_system_state(self):
        """Test system state collection."""
        collector = SystemContextCollector()
        state = collector.collect_system_state()
        
        assert 'timestamp' in state
        assert 'platform' in state
        assert 'hostname' in state
        
        # Check that we got basic system info
        assert state['platform'] in ['Linux', 'Darwin', 'Windows']

    def test_collect_logs(self):
        """Test log collection."""
        collector = SystemContextCollector()
        
        # Test with default log sources (may not exist in test environment)
        logs = collector.collect_logs(max_lines=10)
        
        # Should return a dictionary (even if empty)
        assert isinstance(logs, dict)

    def test_collect_service_status(self):
        """Test service status collection."""
        collector = SystemContextCollector()
        
        # Test with some common services
        services = collector.collect_service_status(['ssh', 'cron'])
        
        # Should return a dictionary
        assert isinstance(services, dict)
        
        # Check structure
        for service_name, service_info in services.items():
            assert 'active' in service_info
            assert 'status' in service_info

    def test_collect_command_errors(self):
        """Test command error collection."""
        collector = SystemContextCollector()
        
        # Test with empty history
        errors = collector.collect_command_errors(None)
        assert errors == []
        
        # Test with some error records
        command_history = [
            {
                'command': 'false',
                'exit_code': 1,
                'error': 'Command failed',
                'stderr': 'Error output'
            },
            {
                'command': 'true',
                'exit_code': 0,
            }
        ]
        
        errors = collector.collect_command_errors(command_history)
        assert len(errors) == 1
        assert errors[0]['command'] == 'false'
        assert errors[0]['exit_code'] == 1

    def test_collect_all(self):
        """Test collecting all context."""
        collector = SystemContextCollector()
        
        context = collector.collect_all()
        
        # Check all expected keys are present
        assert 'collection_timestamp' in context
        assert 'system_state' in context
        assert 'logs' in context
        assert 'service_status' in context
        assert 'command_errors' in context
        
        # Verify context is stored
        assert collector.context == context

    def test_get_context_summary(self):
        """Test context summary generation."""
        collector = SystemContextCollector()
        
        # Before collection
        summary = collector.get_context_summary()
        assert summary == "No context collected yet."
        
        # After collection
        collector.collect_all()
        summary = collector.get_context_summary()
        
        # Should contain system info
        assert len(summary) > 0
        assert 'System:' in summary
