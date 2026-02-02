"""
EdgeMind Agent - Web Server
=============================
واجهة الويب API
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from flask import Flask, request, jsonify, render_template_string
    from flask_cors import CORS
except ImportError:
    Flask = None
    CORS = None

# إضافة المسار للمشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# قالب HTML للواجهة
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EdgeMind Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
        }
        
        header h1 {
            font-size: 2.5rem;
            color: #00d9ff;
            margin-bottom: 10px;
        }
        
        header p {
            color: #888;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .input-section {
            display: flex;
            gap: 10px;
        }
        
        #request-input {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1rem;
        }
        
        #request-input::placeholder {
            color: #666;
        }
        
        #submit-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            border: none;
            border-radius: 10px;
            color: #1a1a2e;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        #submit-btn:hover {
            transform: scale(1.05);
        }
        
        #submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            padding: 15px 20px;
            background: rgba(0,217,255,0.1);
            border-radius: 10px;
            margin-top: 15px;
        }
        
        .status-item {
            text-align: center;
        }
        
        .status-value {
            font-size: 1.5rem;
            color: #00d9ff;
        }
        
        .status-label {
            font-size: 0.8rem;
            color: #888;
        }
        
        #response-area {
            display: none;
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .risk-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .risk-low { background: #00ff88; color: #1a1a2e; }
        .risk-medium { background: #ffaa00; color: #1a1a2e; }
        .risk-high { background: #ff4444; color: #fff; }
        .risk-blocked { background: #ff0000; color: #fff; }
        
        .result-section {
            margin-bottom: 20px;
        }
        
        .result-section h3 {
            color: #00d9ff;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }
        
        .commands-list {
            list-style: none;
        }
        
        .commands-list li {
            background: rgba(0,0,0,0.3);
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 5px;
            font-family: monospace;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .execute-btn {
            padding: 5px 15px;
            background: #00ff88;
            border: none;
            border-radius: 5px;
            color: #1a1a2e;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .execute-btn:hover {
            background: #00cc6a;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.1);
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .plan-list {
            list-style: decimal;
            padding-right: 20px;
        }
        
        .plan-list li {
            margin-bottom: 8px;
            line-height: 1.5;
        }
        
        #output-area {
            display: none;
            margin-top: 20px;
        }
        
        .output-content {
            background: #000;
            padding: 15px;
            border-radius: 10px;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .output-success { border-left: 4px solid #00ff88; }
        .output-error { border-left: 4px solid #ff4444; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 EdgeMind Agent</h1>
            <p>AI System Agent for Raspberry Pi OS</p>
        </header>
        
        <div class="card">
            <div class="input-section">
                <input type="text" id="request-input" placeholder="اكتب طلبك هنا... مثال: ما هي حالة الذاكرة؟">
                <button id="submit-btn" onclick="submitRequest()">تحليل</button>
            </div>
            
            <div class="status-bar" id="status-bar">
                <div class="status-item">
                    <div class="status-value" id="hostname">-</div>
                    <div class="status-label">المضيف</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="memory">-</div>
                    <div class="status-label">الذاكرة</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="cpu">-</div>
                    <div class="status-label">المعالج</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="disk">-</div>
                    <div class="status-label">القرص</div>
                </div>
            </div>
        </div>
        
        <div class="card" id="loading" style="display: none;">
            <div class="loading">
                <div class="spinner"></div>
                <p>🧠 جاري التحليل...</p>
            </div>
        </div>
        
        <div class="card" id="response-area">
            <div class="result-header">
                <h2 id="intent">-</h2>
                <span class="risk-badge risk-low" id="risk-badge">منخفض</span>
            </div>
            
            <div class="result-section">
                <h3>📊 التشخيص</h3>
                <p id="diagnosis">-</p>
            </div>
            
            <div class="result-section">
                <h3>📋 الخطة</h3>
                <ol class="plan-list" id="plan"></ol>
            </div>
            
            <div class="result-section">
                <h3>💻 الأوامر المقترحة</h3>
                <ul class="commands-list" id="commands"></ul>
            </div>
            
            <div class="result-section" id="security-section" style="display: none;">
                <h3>🔒 ملاحظة أمنية</h3>
                <p id="security-note" style="color: #ffaa00;">-</p>
            </div>
        </div>
        
        <div class="card" id="output-area">
            <h3>📤 ناتج التنفيذ</h3>
            <div class="output-content output-success" id="output-content"></div>
        </div>
    </div>
    
    <script>
        // تحميل الحالة
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('hostname').textContent = data.hostname || '-';
                document.getElementById('memory').textContent = data.memory_percent ? data.memory_percent + '%' : '-';
                document.getElementById('cpu').textContent = data.cpu_percent ? data.cpu_percent + '%' : '-';
                document.getElementById('disk').textContent = data.disk_percent ? data.disk_percent + '%' : '-';
            } catch (e) {
                console.error('Failed to load status:', e);
            }
        }
        
        // إرسال الطلب
        async function submitRequest() {
            const input = document.getElementById('request-input');
            const request = input.value.trim();
            
            if (!request) return;
            
            // إظهار التحميل
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response-area').style.display = 'none';
            document.getElementById('output-area').style.display = 'none';
            document.getElementById('submit-btn').disabled = true;
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ request: request })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayResult(data.decision);
                } else {
                    alert('خطأ: ' + data.error);
                }
            } catch (e) {
                alert('خطأ في الاتصال: ' + e.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('submit-btn').disabled = false;
            }
        }
        
        // عرض النتيجة
        function displayResult(decision) {
            document.getElementById('response-area').style.display = 'block';
            
            // النية
            document.getElementById('intent').textContent = decision.intent || '-';
            
            // الخطورة
            const riskBadge = document.getElementById('risk-badge');
            const risk = decision.risk || 'low';
            riskBadge.className = 'risk-badge risk-' + risk;
            riskBadge.textContent = {
                'low': 'منخفض',
                'medium': 'متوسط',
                'high': 'عالي',
                'blocked': 'محظور'
            }[risk] || risk;
            
            // التشخيص
            document.getElementById('diagnosis').textContent = decision.diagnosis || '-';
            
            // الخطة
            const planList = document.getElementById('plan');
            planList.innerHTML = '';
            (decision.plan || []).forEach(step => {
                const li = document.createElement('li');
                li.textContent = step;
                planList.appendChild(li);
            });
            
            // الأوامر
            const commandsList = document.getElementById('commands');
            commandsList.innerHTML = '';
            (decision.commands_proposed || []).forEach(cmd => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <code>${cmd}</code>
                    ${decision.is_executable ? '<button class="execute-btn" onclick="executeCommand(\\''+cmd.replace(/'/g, "\\'")+'\\')" >تنفيذ</button>' : ''}
                `;
                commandsList.appendChild(li);
            });
            
            // الملاحظة الأمنية
            const securitySection = document.getElementById('security-section');
            if (decision.security_note) {
                securitySection.style.display = 'block';
                document.getElementById('security-note').textContent = decision.security_note;
            } else {
                securitySection.style.display = 'none';
            }
        }
        
        // تنفيذ أمر
        async function executeCommand(command) {
            if (!confirm('هل تريد تنفيذ هذا الأمر؟\\n\\n' + command)) return;
            
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });
                
                const data = await response.json();
                
                const outputArea = document.getElementById('output-area');
                const outputContent = document.getElementById('output-content');
                
                outputArea.style.display = 'block';
                outputContent.className = 'output-content ' + (data.success ? 'output-success' : 'output-error');
                outputContent.textContent = data.stdout || data.stderr || data.block_reason || 'لا يوجد ناتج';
                
            } catch (e) {
                alert('خطأ في التنفيذ: ' + e.message);
            }
        }
        
        // Enter للإرسال
        document.getElementById('request-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitRequest();
        });
        
        // تحميل الحالة عند البدء
        loadStatus();
        setInterval(loadStatus, 30000); // تحديث كل 30 ثانية
    </script>
</body>
</html>
"""


def create_app(api_key: Optional[str] = None) -> 'Flask':
    """
    إنشاء تطبيق Flask
    
    Args:
        api_key: مفتاح Gemini API
    
    Returns:
        Flask app
    """
    if Flask is None:
        raise ImportError("Flask required. Install with: pip install flask flask-cors")
    
    app = Flask(__name__)
    CORS(app)
    
    # تهيئة Agent
    agent = None
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    if api_key:
        try:
            from src.core import EdgeMindAgent
            agent = EdgeMindAgent(api_key=api_key, strict_mode=True)
        except Exception as e:
            print(f"Warning: Could not initialize agent: {e}")
    
    # تهيئة Context Builder و Gateway
    from src.core import ContextBuilder
    from src.gateway import SecurityGateway
    
    context_builder = ContextBuilder()
    gateway = SecurityGateway(strict_mode=True)
    
    @app.route('/')
    def index():
        """الصفحة الرئيسية"""
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/api/status')
    def get_status():
        """الحصول على حالة النظام"""
        try:
            status = context_builder.build_minimal()
            return jsonify(status)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/context')
    def get_context():
        """الحصول على السياق الكامل"""
        try:
            context = context_builder.build()
            return jsonify(context.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/analyze', methods=['POST'])
    def analyze():
        """تحليل طلب"""
        if not agent:
            return jsonify({
                "success": False,
                "error": "Agent not initialized. Set GEMINI_API_KEY."
            }), 500
        
        data = request.get_json()
        user_request = data.get('request', '')
        
        if not user_request:
            return jsonify({
                "success": False,
                "error": "Request is required"
            }), 400
        
        try:
            response = agent.process(
                user_request=user_request,
                include_context=True,
                execute_commands=False
            )
            
            if response.success:
                return jsonify({
                    "success": True,
                    "decision": response.decision.to_dict() if response.decision else None
                })
            else:
                return jsonify({
                    "success": False,
                    "error": response.error
                }), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/api/execute', methods=['POST'])
    def execute():
        """تنفيذ أمر"""
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({
                "success": False,
                "error": "Command is required"
            }), 400
        
        try:
            result = gateway.execute(command)
            return jsonify(result.to_dict())
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/api/validate', methods=['POST'])
    def validate():
        """التحقق من أمر"""
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({
                "success": False,
                "error": "Command is required"
            }), 400
        
        is_valid, reason, risk = gateway.validate_command(command)
        
        return jsonify({
            "command": command,
            "valid": is_valid,
            "reason": reason,
            "risk": risk
        })
    
    @app.route('/api/health')
    def health():
        """فحص صحة الخدمة"""
        return jsonify({
            "status": "healthy",
            "agent_ready": agent is not None,
            "timestamp": datetime.now().isoformat()
        })
    
    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    debug: bool = False,
    api_key: Optional[str] = None
):
    """
    تشغيل الخادم
    
    Args:
        host: عنوان الاستماع
        port: المنفذ
        debug: وضع التصحيح
        api_key: مفتاح API
    """
    app = create_app(api_key)
    
    print(f"""
╔═══════════════════════════════════════════════════════╗
║          EdgeMind Agent - Web Server                   ║
╠═══════════════════════════════════════════════════════╣
║  🌐 URL: http://{host}:{port}                          
║  📊 API: http://{host}:{port}/api/                     
║  🔧 Debug: {debug}                                     
╚═══════════════════════════════════════════════════════╝
    """)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EdgeMind Agent Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--api-key", help="Gemini API Key")
    
    args = parser.parse_args()
    
    run_server(
        host=args.host,
        port=args.port,
        debug=args.debug,
        api_key=args.api_key
    )
