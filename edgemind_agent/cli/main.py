"""Command-line interface for EdgeMind Agent."""

import argparse
import logging
import sys
import json
from typing import Optional
import os

from edgemind_agent.context.collector import SystemContextCollector
from edgemind_agent.security.policy import SecurityPolicy
from edgemind_agent.execution.gateway import SafeExecutionGateway


# Try to import AI brain, but make it optional
try:
    from edgemind_agent.ai.gemini_client import GeminiAIBrain
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    GeminiAIBrain = None


logger = logging.getLogger(__name__)


class EdgeMindCLI:
    """Command-line interface for EdgeMind Agent."""

    def __init__(self):
        """Initialize the CLI."""
        self.context_collector = SystemContextCollector()
        self.security_policy = SecurityPolicy(strict_mode=True)
        self.execution_gateway = SafeExecutionGateway(dry_run=False)
        self.ai_brain: Optional[GeminiAIBrain] = None

    def setup_logging(self, verbose: bool = False):
        """Set up logging configuration.
        
        Args:
            verbose: If True, enable debug logging.
        """
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )

    def initialize_ai(self, api_key: Optional[str] = None) -> bool:
        """Initialize the AI brain.
        
        Args:
            api_key: Optional Gemini API key.
            
        Returns:
            True if initialized successfully.
        """
        if not AI_AVAILABLE:
            logger.error("AI brain not available. Install google-generativeai package.")
            return False
        
        try:
            self.ai_brain = GeminiAIBrain(api_key=api_key)
            logger.info("AI brain initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AI brain: {e}")
            return False

    def collect_context(self, args: argparse.Namespace) -> dict:
        """Collect system context.
        
        Args:
            args: Command-line arguments.
            
        Returns:
            Collected context dictionary.
        """
        logger.info("Collecting system context...")
        
        log_sources = None
        if args.logs:
            log_sources = args.logs.split(',')
        
        services = None
        if args.services:
            services = args.services.split(',')
        
        context = self.context_collector.collect_all(
            log_sources=log_sources,
            services=services,
            command_history=self.execution_gateway.get_execution_history()
        )
        
        logger.info("Context collection complete")
        return context

    def analyze_system(self, args: argparse.Namespace) -> int:
        """Analyze system and provide recommendations.
        
        Args:
            args: Command-line arguments.
            
        Returns:
            Exit code (0 for success).
        """
        # Collect context
        context = self.collect_context(args)
        
        # Show context summary
        summary = self.context_collector.get_context_summary()
        print(f"\n{'='*60}")
        print(f"SYSTEM CONTEXT SUMMARY")
        print(f"{'='*60}")
        print(summary)
        print(f"{'='*60}\n")
        
        # If output file specified, save context
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(context, f, indent=2, default=str)
            logger.info(f"Context saved to {args.output}")
        
        # If AI is enabled, perform analysis
        if args.ai and self.ai_brain:
            logger.info("Performing AI analysis...")
            analysis = self.ai_brain.analyze_system_state(context)
            
            if analysis['status'] == 'success':
                print(f"\n{'='*60}")
                print(f"AI ANALYSIS")
                print(f"{'='*60}")
                analysis_data = analysis['analysis']
                
                print(f"\nSUMMARY: {analysis_data.get('summary', 'N/A')}")
                
                print(f"\nISSUES DETECTED:")
                issues = analysis_data.get('issues', [])
                if issues:
                    for i, issue in enumerate(issues, 1):
                        print(f"  {i}. [{issue['severity']}] {issue['description']}")
                        print(f"     Category: {issue['category']}")
                else:
                    print("  No issues detected")
                
                print(f"\nRECOMMENDATIONS:")
                recommendations = analysis_data.get('recommendations', [])
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        print(f"  {i}. [Priority: {rec['priority']}] {rec['action']}")
                        print(f"     For: {rec['issue']}")
                else:
                    print("  No recommendations")
                
                print(f"{'='*60}\n")
                
                # Save analysis if output file specified
                if args.output:
                    analysis_file = args.output.replace('.json', '_analysis.json')
                    with open(analysis_file, 'w') as f:
                        json.dump(analysis, f, indent=2, default=str)
                    logger.info(f"Analysis saved to {analysis_file}")
            else:
                logger.error(f"AI analysis failed: {analysis.get('error', 'Unknown error')}")
                return 1
        
        return 0

    def plan_actions(self, args: argparse.Namespace) -> int:
        """Create an action plan based on system analysis.
        
        Args:
            args: Command-line arguments.
            
        Returns:
            Exit code (0 for success).
        """
        if not self.ai_brain:
            logger.error("AI brain not initialized. Use --ai flag and set GEMINI_API_KEY")
            return 1
        
        # Collect context
        context = self.collect_context(args)
        
        # Analyze system
        logger.info("Analyzing system state...")
        analysis = self.ai_brain.analyze_system_state(context)
        
        if analysis['status'] != 'success':
            logger.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
            return 1
        
        # Create action plan
        logger.info("Creating action plan...")
        plan_result = self.ai_brain.plan_actions(analysis, context)
        
        if plan_result['status'] != 'success':
            logger.error(f"Planning failed: {plan_result.get('error', 'Unknown error')}")
            return 1
        
        plan = plan_result['plan']
        
        # Validate the plan
        logger.info("Validating action plan against security policy...")
        validation = self.security_policy.validate_action_plan(plan)
        
        # Display the plan
        print(f"\n{'='*60}")
        print(f"ACTION PLAN")
        print(f"{'='*60}")
        print(f"Overall Risk: {plan.get('overall_risk', 'UNKNOWN')}")
        print(f"Requires Approval: {plan.get('requires_approval', False)}")
        print(f"Security Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
        print(f"Highest Risk Level: {validation.get('highest_risk', 'UNKNOWN')}")
        print(f"{'='*60}\n")
        
        for step in plan.get('plan', []):
            print(f"STEP {step['step']}: {step['description']}")
            print(f"  Reasoning: {step['reasoning']}")
            print(f"  Commands:")
            for cmd in step['commands']:
                # Find validation for this command
                cmd_validation = None
                for vstep in validation['validated_steps']:
                    if vstep['step'] == step['step']:
                        for vcmd in vstep['commands']:
                            if vcmd['command'] == cmd:
                                cmd_validation = vcmd
                                break
                
                if cmd_validation:
                    status = "✓ ALLOWED" if cmd_validation['allowed'] else "✗ BLOCKED"
                    risk = cmd_validation['risk_level']
                    print(f"    [{status}] [{risk}] {cmd}")
                else:
                    print(f"    [? UNKNOWN] {cmd}")
            
            print(f"  Risks: {step.get('risks', 'None specified')}")
            print(f"  Verification: {step.get('verification', 'None specified')}")
            print()
        
        # Save plan if output specified
        if args.output:
            plan_file = args.output.replace('.json', '_plan.json')
            with open(plan_file, 'w') as f:
                json.dump({
                    'plan': plan,
                    'validation': validation
                }, f, indent=2, default=str)
            logger.info(f"Plan saved to {plan_file}")
        
        # Ask for execution confirmation if execute flag is set
        if args.execute:
            if not validation['valid']:
                print("ERROR: Cannot execute plan - security validation failed")
                return 1
            
            if validation.get('requires_approval', False):
                response = input("\nThis plan requires approval due to high risk. Execute? (yes/no): ")
                if response.lower() != 'yes':
                    print("Execution cancelled by user")
                    return 0
            
            print("\nExecuting plan...")
            execution_result = self.execution_gateway.execute_plan(validation, require_approval=False)
            
            print(f"\n{'='*60}")
            print(f"EXECUTION RESULTS")
            print(f"{'='*60}")
            print(f"Total Steps: {execution_result['total_steps']}")
            print(f"Failed Steps: {execution_result['failed_steps']}")
            print(f"{'='*60}\n")
            
            for step_result in execution_result['results']:
                print(f"STEP {step_result['step']}: {step_result['description']}")
                for cmd_result in step_result['commands']:
                    status = "SUCCESS" if cmd_result.get('success', False) else "FAILED"
                    print(f"  [{status}] {cmd_result['command']}")
                    if cmd_result.get('stdout'):
                        print(f"    Output: {cmd_result['stdout'][:200]}")
                    if cmd_result.get('stderr'):
                        print(f"    Error: {cmd_result['stderr'][:200]}")
                print()
        
        return 0

    def validate_command(self, args: argparse.Namespace) -> int:
        """Validate a command against security policy.
        
        Args:
            args: Command-line arguments.
            
        Returns:
            Exit code (0 if allowed).
        """
        command = args.command
        
        validation = self.security_policy.validate_command(command)
        
        print(f"\n{'='*60}")
        print(f"COMMAND VALIDATION")
        print(f"{'='*60}")
        print(f"Command: {command}")
        print(f"Allowed: {validation['allowed']}")
        print(f"Risk Level: {validation['risk_level']}")
        print(f"Reason: {validation['reason']}")
        print(f"{'='*60}\n")
        
        return 0 if validation['allowed'] else 1

    def show_status(self, args: argparse.Namespace) -> int:
        """Show EdgeMind Agent status.
        
        Args:
            args: Command-line arguments.
            
        Returns:
            Exit code (0 for success).
        """
        print(f"\n{'='*60}")
        print(f"EDGEMIND AGENT STATUS")
        print(f"{'='*60}")
        
        # Security policy info
        policy_summary = self.security_policy.get_policy_summary()
        print(f"\nSecurity Policy:")
        print(f"  Strict Mode: {policy_summary['strict_mode']}")
        print(f"  Whitelisted Commands: {policy_summary['whitelisted_commands_count']}")
        print(f"  Forbidden Commands: {policy_summary['forbidden_commands_count']}")
        print(f"  Forbidden Patterns: {policy_summary['forbidden_patterns_count']}")
        
        # Execution stats
        exec_stats = self.execution_gateway.get_statistics()
        print(f"\nExecution Statistics:")
        print(f"  Total Executions: {exec_stats['total_executions']}")
        print(f"  Successful: {exec_stats['successful']}")
        print(f"  Failed: {exec_stats['failed']}")
        print(f"  Blocked: {exec_stats['blocked']}")
        if exec_stats['total_executions'] > 0:
            print(f"  Success Rate: {exec_stats['success_rate']:.2%}")
        
        # AI brain info
        print(f"\nAI Brain:")
        if self.ai_brain:
            model_info = self.ai_brain.get_model_info()
            print(f"  Status: Initialized")
            print(f"  Model: {model_info['model_name']}")
        else:
            print(f"  Status: Not initialized")
            print(f"  Available: {AI_AVAILABLE}")
        
        print(f"{'='*60}\n")
        
        return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='EdgeMind Agent - AI System Agent for Raspberry Pi OS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze system with AI
  edgemind-agent analyze --ai
  
  # Create and execute action plan
  edgemind-agent plan --ai --execute
  
  # Validate a command
  edgemind-agent validate "systemctl status ssh"
  
  # Show agent status
  edgemind-agent status
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--ai', action='store_true',
                       help='Enable AI analysis (requires GEMINI_API_KEY)')
    parser.add_argument('--api-key', type=str,
                       help='Gemini API key (overrides GEMINI_API_KEY env var)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze system state')
    analyze_parser.add_argument('-o', '--output', type=str,
                               help='Output file for context data (JSON)')
    analyze_parser.add_argument('--logs', type=str,
                               help='Comma-separated list of log files to collect')
    analyze_parser.add_argument('--services', type=str,
                               help='Comma-separated list of services to check')
    
    # Plan command
    plan_parser = subparsers.add_parser('plan', help='Create action plan')
    plan_parser.add_argument('-o', '--output', type=str,
                            help='Output file for plan (JSON)')
    plan_parser.add_argument('--logs', type=str,
                            help='Comma-separated list of log files to collect')
    plan_parser.add_argument('--services', type=str,
                            help='Comma-separated list of services to check')
    plan_parser.add_argument('--execute', action='store_true',
                            help='Execute the plan after creation')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a command')
    validate_parser.add_argument('command', type=str,
                                help='Command to validate')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show agent status')
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = EdgeMindCLI()
    cli.setup_logging(args.verbose)
    
    # Initialize AI if requested
    if args.ai or args.command == 'plan':
        if not cli.initialize_ai(args.api_key):
            if args.command == 'plan':
                logger.error("AI brain is required for planning")
                return 1
            logger.warning("AI brain initialization failed, continuing without AI")
    
    # Execute command
    if args.command == 'analyze':
        return cli.analyze_system(args)
    elif args.command == 'plan':
        return cli.plan_actions(args)
    elif args.command == 'validate':
        return cli.validate_command(args)
    elif args.command == 'status':
        return cli.show_status(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
