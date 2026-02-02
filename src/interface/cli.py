"""
EdgeMind Agent - CLI Interface
================================
Interactive command-line interface
"""

import os
import sys
import json
from typing import Optional, Dict, Any

try:
    import click
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    click = None
    Console = None

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class EdgeMindCLI:
    """
    Command-line interface for EdgeMind Agent
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the interface
        
        Args:
            api_key: API key (optional)
        """
        if Console is None:
            raise ImportError("rich library is required. Install with: pip install rich")
        
        self.console = Console()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.agent = None
        self._init_agent()
    
    def _init_agent(self):
        """Initialize Agent"""
        try:
            from src.core import EdgeMindAgent
            self.agent = EdgeMindAgent(
                api_key=self.api_key,
                strict_mode=True,
                auto_execute=False
            )
        except Exception as e:
            self.console.print(f"[red]❌ Failed to initialize agent: {e}[/red]")
            self.agent = None
    
    def print_banner(self):
        """Print system banner"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███████╗██████╗  ██████╗ ███████╗███╗   ███╗██╗███╗   ██║
║   ██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗ ████║██║████╗  ██║
║   █████╗  ██║  ██║██║  ███╗█████╗  ██╔████╔██║██║██╔██╗ ██║
║   ██╔══╝  ██║  ██║██║   ██║██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║
║   ███████╗██████╔╝╚██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║
║   ╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══║
║                                                           ║
║            EdgeMind Agent v1.0.0                          ║
║       AI System Agent for Raspberry Pi OS                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(Panel(banner, style="cyan"))
    
    def print_help(self):
        """Print help"""
        help_text = """
## Available Commands

| Command | Description |
|-------|-------|
| `help` | Show this help |
| `status` | Show system status |
| `context` | Show current context |
| `history` | Show session history |
| `execute <command>` | Execute a command directly |
| `clear` | Clear screen |
| `exit` / `quit` | Exit |

## How to Use

Type your question or request naturally, such as:
- "What is the memory status?"
- "I want to check SSH service"
- "Why is the network slow?"

The system will analyze your request and suggest solutions.
        """
        self.console.print(Markdown(help_text))
    
    def print_status(self):
        """Print system status"""
        from src.core import ContextBuilder
        
        builder = ContextBuilder()
        context = builder.build_minimal()
        
        table = Table(title="System Status", show_header=True)
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Hostname", context.get("hostname", "N/A"))
        table.add_row("Raspberry Pi", "✅ Yes" if context.get("is_raspberry_pi") else "❌ No")
        table.add_row("Memory %", f"{context.get('memory_percent', 'N/A')}%")
        table.add_row("CPU %", f"{context.get('cpu_percent', 'N/A')}%")
        table.add_row("Disk %", f"{context.get('disk_percent', 'N/A')}%")
        table.add_row("Time", context.get("timestamp", "N/A"))
        
        self.console.print(table)
    
    def print_context(self):
        """Print full context"""
        from src.core import ContextBuilder
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task("Gathering system information...", total=None)
            
            builder = ContextBuilder()
            context = builder.build()
        
        json_str = json.dumps(context.to_dict(), indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title="System Context", expand=False))
    
    def print_decision(self, decision: Dict[str, Any]):
        """Print system decision"""
        # Color based on risk
        risk_colors = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "blocked": "red"
        }
        
        risk = decision.get("risk", "unknown")
        color = risk_colors.get(risk, "white")
        
        # Decision table
        table = Table(title="Request Analysis", show_header=True)
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        
        table.add_row("Intent", decision.get("intent", "N/A"))
        table.add_row("Category", decision.get("category", "N/A"))
        table.add_row("Risk", f"[{color}]{risk}[/{color}]")
        table.add_row("Diagnosis", decision.get("diagnosis", "N/A"))
        table.add_row("Execution Mode", decision.get("execution_mode", "N/A"))
        
        if decision.get("security_note"):
            table.add_row("Security Note", f"[yellow]{decision['security_note']}[/yellow]")
        
        self.console.print(table)
        
        # Plan
        if decision.get("plan"):
            self.console.print("\n[bold cyan]📋 Plan:[/bold cyan]")
            for i, step in enumerate(decision["plan"], 1):
                self.console.print(f"  {i}. {step}")
        
        # Proposed commands
        if decision.get("commands_proposed"):
            self.console.print("\n[bold cyan]💻 Proposed Commands:[/bold cyan]")
            for cmd in decision["commands_proposed"]:
                self.console.print(f"  [dim]$[/dim] [green]{cmd}[/green]")
    
    def process_request(self, request: str) -> Optional[Dict[str, Any]]:
        """
        Process user request
        
        Args:
            request: The request
        
        Returns:
            Decision or None
        """
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized. Make sure GEMINI_API_KEY is set[/red]")
            return None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task("🧠 Analyzing...", total=None)
            
            response = self.agent.process(
                user_request=request,
                include_context=True,
                execute_commands=False
            )
        
        if not response.success:
            self.console.print(f"[red]❌ Error: {response.error}[/red]")
            return None
        
        return response.decision.to_dict() if response.decision else None
    
    def execute_command(self, command: str):
        """Execute a direct command"""
        from src.gateway import SecurityGateway
        
        gateway = SecurityGateway(strict_mode=True)
        
        # Validate first
        is_valid, reason, risk = gateway.validate_command(command)
        
        if not is_valid:
            self.console.print(f"[red]❌ Command rejected: {reason}[/red]")
            return
        
        if risk == "medium":
            confirm = Confirm.ask(
                f"[yellow]⚠️ This command has medium risk ({risk}). Continue?[/yellow]"
            )
            if not confirm:
                return
        
        # Execute
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task("⚙️ Executing...", total=None)
            result = gateway.execute(command)
        
        if result.success:
            self.console.print(f"[green]✅ Executed successfully[/green]")
            if result.stdout:
                self.console.print(Panel(result.stdout, title="Output"))
        else:
            self.console.print(f"[red]❌ Execution failed[/red]")
            if result.stderr:
                self.console.print(Panel(result.stderr, title="Error", style="red"))
    
    def confirm_and_execute(self, decision: Dict[str, Any]):
        """Confirm and execute commands"""
        commands = decision.get("commands_proposed", [])
        
        if not commands:
            self.console.print("[yellow]No commands to execute[/yellow]")
            return
        
        if not decision.get("is_executable", False):
            self.console.print("[red]❌ These commands are not executable[/red]")
            return
        
        # Show commands
        self.console.print("\n[bold]Commands to execute:[/bold]")
        for i, cmd in enumerate(commands, 1):
            self.console.print(f"  {i}. [cyan]{cmd}[/cyan]")
        
        # Confirm
        if decision.get("requires_confirmation", False):
            confirm = Confirm.ask("\n[yellow]⚠️ Do you want to execute these commands?[/yellow]")
            if not confirm:
                self.console.print("[dim]Cancelled[/dim]")
                return
        
        # Execute
        for cmd in commands:
            self.execute_command(cmd)
    
    def run_interactive(self):
        """Run interactive mode"""
        self.print_banner()
        self.console.print("[dim]Type 'help' for assistance or 'exit' to quit[/dim]\n")
        
        while True:
            try:
                # Read input
                user_input = Prompt.ask("[bold cyan]EdgeMind[/bold cyan]")
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                # Special commands
                if user_input.lower() in ["exit", "quit", "q"]:
                    self.console.print("[dim]Goodbye! 👋[/dim]")
                    break
                
                elif user_input.lower() == "help":
                    self.print_help()
                
                elif user_input.lower() == "status":
                    self.print_status()
                
                elif user_input.lower() == "context":
                    self.print_context()
                
                elif user_input.lower() == "clear":
                    self.console.clear()
                
                elif user_input.lower() == "history":
                    if self.agent:
                        history = self.agent.get_session_stats()
                        self.console.print(json.dumps(history, indent=2, ensure_ascii=False))
                
                elif user_input.lower().startswith("execute "):
                    cmd = user_input[8:].strip()
                    self.execute_command(cmd)
                
                else:
                    # Process as request
                    decision = self.process_request(user_input)
                    
                    if decision:
                        self.print_decision(decision)
                        
                        # Ask about execution
                        if decision.get("commands_proposed") and decision.get("is_executable"):
                            execute = Confirm.ask("\n[bold]Do you want to execute the proposed commands?[/bold]")
                            if execute:
                                self.confirm_and_execute(decision)
                
                self.console.print()  # Empty line
                
            except KeyboardInterrupt:
                self.console.print("\n[dim]Ctrl+C - Type 'exit' to quit[/dim]")
            
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")


# Entry point
@click.group() if click else lambda: None
def cli():
    """EdgeMind Agent - AI System Agent for Raspberry Pi OS"""
    pass


@cli.command() if click else lambda: None
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API Key')
def interactive(api_key):
    """Run interactive mode"""
    app = EdgeMindCLI(api_key=api_key)
    app.run_interactive()


@cli.command() if click else lambda: None
def status():
    """Show system status"""
    app = EdgeMindCLI()
    app.print_status()


@cli.command() if click else lambda: None
@click.argument('request')
@click.option('--execute', is_flag=True, help='Execute proposed commands')
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API Key')
def analyze(request, execute, api_key):
    """Analyze a request"""
    app = EdgeMindCLI(api_key=api_key)
    decision = app.process_request(request)
    
    if decision:
        app.print_decision(decision)
        if execute:
            app.confirm_and_execute(decision)


if __name__ == "__main__":
    if click:
        cli()
    else:
        print("Click library required. Install with: pip install click rich")
