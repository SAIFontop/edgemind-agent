#!/usr/bin/env python3
"""
EdgeMind Agent - Main Entry Point
===================================

AI System Agent for Raspberry Pi OS

Usage:
    python main.py                  # Interactive CLI mode
    python main.py --web            # Web server mode
    python main.py --status         # Show system status
    python main.py --analyze "..."  # Analyze a request
"""

import os
import sys
import argparse
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """فحص المتطلبات"""
    missing = []
    
    try:
        import yaml
    except ImportError:
        missing.append("pyyaml")
    
    try:
        import click
    except ImportError:
        missing.append("click")
    
    try:
        from rich.console import Console
    except ImportError:
        missing.append("rich")
    
    if missing:
        print("⚠️  Missing dependencies. Install with:")
        print(f"   pip install {' '.join(missing)}")
        print("\nOr install all requirements:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def print_banner():
    """طباعة شعار البداية"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ███████╗██████╗  ██████╗ ███████╗███╗   ███╗██╗███╗  ██║
    ║   ██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗ ████║██║████╗ ██║
    ║   █████╗  ██║  ██║██║  ███╗█████╗  ██╔████╔██║██║██╔██╗██║
    ║   ██╔══╝  ██║  ██║██║   ██║██╔══╝  ██║╚██╔╝██║██║██║╚██╗█║
    ║   ███████╗██████╔╝╚██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚███║
    ║   ╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚══║
    ║                                                           ║
    ║             EdgeMind Agent v1.0.0                         ║
    ║        AI System Agent for Raspberry Pi OS                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_cli(api_key: str = None):
    """تشغيل واجهة سطر الأوامر"""
    from src.interface import EdgeMindCLI
    
    cli = EdgeMindCLI(api_key=api_key)
    cli.run_interactive()


def run_web(host: str = "0.0.0.0", port: int = 8080, api_key: str = None):
    """تشغيل خادم الويب"""
    from src.interface import run_server
    
    run_server(host=host, port=port, api_key=api_key)


def show_status():
    """عرض حالة النظام"""
    from src.core import ContextBuilder
    import json
    
    builder = ContextBuilder()
    context = builder.build()
    
    print("\n📊 System Status:")
    print("=" * 50)
    print(json.dumps(context.to_dict(), indent=2, ensure_ascii=False))


def analyze_request(request: str, api_key: str = None, execute: bool = False):
    """تحليل طلب"""
    from src.core import EdgeMindAgent
    import json
    
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY is required")
        print("   Set it with: export GEMINI_API_KEY=your-key")
        return
    
    print(f"\n🔍 Analyzing: {request}")
    print("=" * 50)
    
    agent = EdgeMindAgent(api_key=api_key)
    response = agent.process(
        user_request=request,
        include_context=True,
        execute_commands=execute
    )
    
    if response.success:
        print("\n✅ Analysis Complete:")
        print(json.dumps(response.decision.to_dict(), indent=2, ensure_ascii=False))
        
        if response.execution_results:
            print("\n📤 Execution Results:")
            for result in response.execution_results:
                print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\n❌ Error: {response.error}")


def main():
    """نقطة الدخول الرئيسية"""
    parser = argparse.ArgumentParser(
        description="EdgeMind Agent - AI System Agent for Raspberry Pi OS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Interactive CLI mode
  python main.py --web              # Web server mode
  python main.py --web --port 3000  # Web server on port 3000
  python main.py --status           # Show system status
  python main.py --analyze "check memory"  # Analyze request
  python main.py --analyze "check ssh" --execute  # Analyze and execute
        """
    )
    
    # وضع التشغيل
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--web",
        action="store_true",
        help="Run web server mode"
    )
    mode_group.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    mode_group.add_argument(
        "--analyze",
        type=str,
        metavar="REQUEST",
        help="Analyze a specific request"
    )
    
    # خيارات الويب
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Web server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Web server port (default: 8080)"
    )
    
    # خيارات عامة
    parser.add_argument(
        "--api-key",
        type=str,
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute proposed commands (use with --analyze)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="EdgeMind Agent v1.0.0"
    )
    
    args = parser.parse_args()
    
    # فحص المتطلبات
    if not check_dependencies():
        sys.exit(1)
    
    # الحصول على API key
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    
    # تنفيذ الوضع المطلوب
    if args.status:
        show_status()
    
    elif args.analyze:
        analyze_request(args.analyze, api_key, args.execute)
    
    elif args.web:
        print_banner()
        run_web(host=args.host, port=args.port, api_key=api_key)
    
    else:
        # الوضع الافتراضي: CLI تفاعلي
        run_cli(api_key=api_key)


if __name__ == "__main__":
    main()
