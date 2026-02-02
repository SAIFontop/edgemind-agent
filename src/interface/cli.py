"""
EdgeMind Agent - CLI Interface
================================
واجهة سطر الأوامر التفاعلية
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

# إضافة المسار للمشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class EdgeMindCLI:
    """
    واجهة سطر الأوامر لـ EdgeMind Agent
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        تهيئة الواجهة
        
        Args:
            api_key: مفتاح API (اختياري)
        """
        if Console is None:
            raise ImportError("rich library is required. Install with: pip install rich")
        
        self.console = Console()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.agent = None
        self._init_agent()
    
    def _init_agent(self):
        """تهيئة Agent"""
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
        """طباعة شعار النظام"""
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
        """طباعة المساعدة"""
        help_text = """
## الأوامر المتاحة

| الأمر | الوصف |
|-------|-------|
| `help` | عرض هذه المساعدة |
| `status` | عرض حالة النظام |
| `context` | عرض السياق الحالي |
| `history` | عرض تاريخ الجلسة |
| `execute <command>` | تنفيذ أمر مباشرة |
| `clear` | مسح الشاشة |
| `exit` / `quit` | الخروج |

## كيفية الاستخدام

اكتب سؤالك أو طلبك بشكل طبيعي، مثل:
- "ما هي حالة الذاكرة؟"
- "أريد فحص خدمة SSH"
- "لماذا الشبكة بطيئة؟"

النظام سيحلل طلبك ويقترح الحلول.
        """
        self.console.print(Markdown(help_text))
    
    def print_status(self):
        """طباعة حالة النظام"""
        from src.core import ContextBuilder
        
        builder = ContextBuilder()
        context = builder.build_minimal()
        
        table = Table(title="حالة النظام", show_header=True)
        table.add_column("العنصر", style="cyan")
        table.add_column("القيمة", style="green")
        
        table.add_row("المضيف", context.get("hostname", "N/A"))
        table.add_row("Raspberry Pi", "✅ نعم" if context.get("is_raspberry_pi") else "❌ لا")
        table.add_row("الذاكرة %", f"{context.get('memory_percent', 'N/A')}%")
        table.add_row("المعالج %", f"{context.get('cpu_percent', 'N/A')}%")
        table.add_row("القرص %", f"{context.get('disk_percent', 'N/A')}%")
        table.add_row("الوقت", context.get("timestamp", "N/A"))
        
        self.console.print(table)
    
    def print_context(self):
        """طباعة السياق الكامل"""
        from src.core import ContextBuilder
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task("جمع معلومات النظام...", total=None)
            
            builder = ContextBuilder()
            context = builder.build()
        
        json_str = json.dumps(context.to_dict(), indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title="سياق النظام", expand=False))
    
    def print_decision(self, decision: Dict[str, Any]):
        """طباعة قرار النظام"""
        # لون حسب الخطورة
        risk_colors = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "blocked": "red"
        }
        
        risk = decision.get("risk", "unknown")
        color = risk_colors.get(risk, "white")
        
        # جدول القرار
        table = Table(title="تحليل الطلب", show_header=True)
        table.add_column("الحقل", style="cyan")
        table.add_column("القيمة")
        
        table.add_row("النية", decision.get("intent", "N/A"))
        table.add_row("التصنيف", decision.get("category", "N/A"))
        table.add_row("الخطورة", f"[{color}]{risk}[/{color}]")
        table.add_row("التشخيص", decision.get("diagnosis", "N/A"))
        table.add_row("وضع التنفيذ", decision.get("execution_mode", "N/A"))
        
        if decision.get("security_note"):
            table.add_row("ملاحظة أمنية", f"[yellow]{decision['security_note']}[/yellow]")
        
        self.console.print(table)
        
        # الخطة
        if decision.get("plan"):
            self.console.print("\n[bold cyan]📋 الخطة:[/bold cyan]")
            for i, step in enumerate(decision["plan"], 1):
                self.console.print(f"  {i}. {step}")
        
        # الأوامر المقترحة
        if decision.get("commands_proposed"):
            self.console.print("\n[bold cyan]💻 الأوامر المقترحة:[/bold cyan]")
            for cmd in decision["commands_proposed"]:
                self.console.print(f"  [dim]$[/dim] [green]{cmd}[/green]")
    
    def process_request(self, request: str) -> Optional[Dict[str, Any]]:
        """
        معالجة طلب المستخدم
        
        Args:
            request: الطلب
        
        Returns:
            القرار أو None
        """
        if not self.agent:
            self.console.print("[red]❌ Agent غير مُهيأ. تأكد من GEMINI_API_KEY[/red]")
            return None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task("🧠 جاري التحليل...", total=None)
            
            response = self.agent.process(
                user_request=request,
                include_context=True,
                execute_commands=False
            )
        
        if not response.success:
            self.console.print(f"[red]❌ خطأ: {response.error}[/red]")
            return None
        
        return response.decision.to_dict() if response.decision else None
    
    def execute_command(self, command: str):
        """تنفيذ أمر مباشر"""
        from src.gateway import SecurityGateway
        
        gateway = SecurityGateway(strict_mode=True)
        
        # التحقق أولاً
        is_valid, reason, risk = gateway.validate_command(command)
        
        if not is_valid:
            self.console.print(f"[red]❌ الأمر مرفوض: {reason}[/red]")
            return
        
        if risk == "medium":
            confirm = Confirm.ask(
                f"[yellow]⚠️ هذا الأمر متوسط الخطورة ({risk}). متابعة؟[/yellow]"
            )
            if not confirm:
                return
        
        # تنفيذ
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task("⚙️ جاري التنفيذ...", total=None)
            result = gateway.execute(command)
        
        if result.success:
            self.console.print(f"[green]✅ تم التنفيذ بنجاح[/green]")
            if result.stdout:
                self.console.print(Panel(result.stdout, title="الناتج"))
        else:
            self.console.print(f"[red]❌ فشل التنفيذ[/red]")
            if result.stderr:
                self.console.print(Panel(result.stderr, title="الخطأ", style="red"))
    
    def confirm_and_execute(self, decision: Dict[str, Any]):
        """تأكيد وتنفيذ الأوامر"""
        commands = decision.get("commands_proposed", [])
        
        if not commands:
            self.console.print("[yellow]لا توجد أوامر للتنفيذ[/yellow]")
            return
        
        if not decision.get("is_executable", False):
            self.console.print("[red]❌ هذه الأوامر غير قابلة للتنفيذ[/red]")
            return
        
        # عرض الأوامر
        self.console.print("\n[bold]الأوامر للتنفيذ:[/bold]")
        for i, cmd in enumerate(commands, 1):
            self.console.print(f"  {i}. [cyan]{cmd}[/cyan]")
        
        # تأكيد
        if decision.get("requires_confirmation", False):
            confirm = Confirm.ask("\n[yellow]⚠️ هل تريد تنفيذ هذه الأوامر؟[/yellow]")
            if not confirm:
                self.console.print("[dim]تم الإلغاء[/dim]")
                return
        
        # تنفيذ
        for cmd in commands:
            self.execute_command(cmd)
    
    def run_interactive(self):
        """تشغيل الوضع التفاعلي"""
        self.print_banner()
        self.console.print("[dim]اكتب 'help' للمساعدة أو 'exit' للخروج[/dim]\n")
        
        while True:
            try:
                # قراءة الإدخال
                user_input = Prompt.ask("[bold cyan]EdgeMind[/bold cyan]")
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                # أوامر خاصة
                if user_input.lower() in ["exit", "quit", "q"]:
                    self.console.print("[dim]وداعاً! 👋[/dim]")
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
                    # معالجة كطلب
                    decision = self.process_request(user_input)
                    
                    if decision:
                        self.print_decision(decision)
                        
                        # سؤال عن التنفيذ
                        if decision.get("commands_proposed") and decision.get("is_executable"):
                            execute = Confirm.ask("\n[bold]هل تريد تنفيذ الأوامر المقترحة؟[/bold]")
                            if execute:
                                self.confirm_and_execute(decision)
                
                self.console.print()  # سطر فارغ
                
            except KeyboardInterrupt:
                self.console.print("\n[dim]Ctrl+C - اكتب 'exit' للخروج[/dim]")
            
            except Exception as e:
                self.console.print(f"[red]❌ خطأ: {e}[/red]")


# نقطة الدخول
@click.group() if click else lambda: None
def cli():
    """EdgeMind Agent - AI System Agent for Raspberry Pi OS"""
    pass


@cli.command() if click else lambda: None
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API Key')
def interactive(api_key):
    """تشغيل الوضع التفاعلي"""
    app = EdgeMindCLI(api_key=api_key)
    app.run_interactive()


@cli.command() if click else lambda: None
def status():
    """عرض حالة النظام"""
    app = EdgeMindCLI()
    app.print_status()


@cli.command() if click else lambda: None
@click.argument('request')
@click.option('--execute', is_flag=True, help='تنفيذ الأوامر المقترحة')
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API Key')
def analyze(request, execute, api_key):
    """تحليل طلب"""
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
