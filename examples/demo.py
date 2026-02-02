#!/usr/bin/env python3
"""
Example script demonstrating EdgeMind Agent usage.
This script shows how to use EdgeMind Agent programmatically.
"""

import sys
import logging
from edgemind_agent import SystemContextCollector, SecurityPolicy, SafeExecutionGateway

# Optional: AI brain (requires API key)
try:
    from edgemind_agent.ai.gemini_client import GeminiAIBrain
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_context_collection():
    """Example: Collect system context."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Context Collection")
    print("="*60)
    
    collector = SystemContextCollector()
    
    # Collect all context
    context = collector.collect_all(
        services=['ssh', 'cron']
    )
    
    # Print summary
    summary = collector.get_context_summary()
    print(f"\n{summary}\n")
    
    # Show some details
    print("System State:")
    state = context['system_state']
    print(f"  Platform: {state.get('platform')}")
    print(f"  Hostname: {state.get('hostname')}")
    if 'load_average' in state:
        la = state['load_average']
        print(f"  Load: {la.get('1min')}, {la.get('5min')}, {la.get('15min')}")
    
    return context


def example_command_validation():
    """Example: Validate commands."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Command Validation")
    print("="*60)
    
    policy = SecurityPolicy(strict_mode=True)
    
    # Test various commands
    test_commands = [
        "ls -la",
        "systemctl status ssh",
        "cat /etc/hosts",
        "rm -rf /",  # Forbidden
        "ping google.com",
        "dd if=/dev/zero of=/dev/sda"  # Forbidden
    ]
    
    print("\nValidating commands:")
    for cmd in test_commands:
        result = policy.validate_command(cmd)
        status = "✓ ALLOWED" if result['allowed'] else "✗ BLOCKED"
        print(f"  {status} [{result['risk_level']}] {cmd}")


def example_safe_execution():
    """Example: Safe command execution."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Safe Command Execution")
    print("="*60)
    
    policy = SecurityPolicy(strict_mode=True)
    gateway = SafeExecutionGateway(dry_run=False)
    
    # Execute safe commands
    safe_commands = [
        "echo 'Hello from EdgeMind Agent'",
        "whoami",
        "uname -a"
    ]
    
    print("\nExecuting safe commands:")
    for cmd in safe_commands:
        validation = policy.validate_command(cmd)
        
        if validation['allowed']:
            result = gateway.execute_command(cmd, validation, timeout=5)
            
            if result.get('success'):
                print(f"  ✓ {cmd}")
                if result.get('stdout'):
                    print(f"    Output: {result['stdout'].strip()[:100]}")
            else:
                print(f"  ✗ {cmd} - Failed")
        else:
            print(f"  ✗ {cmd} - Blocked")
    
    # Show statistics
    print("\nExecution Statistics:")
    stats = gateway.get_statistics()
    print(f"  Total: {stats['total_executions']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Blocked: {stats['blocked']}")


def example_security_policy():
    """Example: Security policy details."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Security Policy")
    print("="*60)
    
    policy = SecurityPolicy(strict_mode=True)
    summary = policy.get_policy_summary()
    
    print(f"\nSecurity Policy Summary:")
    print(f"  Strict Mode: {summary['strict_mode']}")
    print(f"  Whitelisted Commands: {summary['whitelisted_commands_count']}")
    print(f"  Forbidden Commands: {summary['forbidden_commands_count']}")
    print(f"  Forbidden Patterns: {summary['forbidden_patterns_count']}")


def main():
    """Run all examples."""
    setup_logging()
    
    print("="*60)
    print("EdgeMind Agent - Example Usage")
    print("="*60)
    
    try:
        # Run examples
        example_context_collection()
        example_command_validation()
        example_safe_execution()
        example_security_policy()
        
        print("\n" + "="*60)
        print("Examples completed successfully!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
