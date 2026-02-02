"""
EdgeMind Agent - Gemini API Client
===================================
العميل الرسمي للتواصل مع Gemini API
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@dataclass
class GeminiResponse:
    """استجابة Gemini مُهيكلة"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None


class GeminiClient:
    """
    عميل Gemini API لـ EdgeMind Agent
    
    يتعامل مع:
    - إعداد الاتصال
    - إرسال السياق والطلبات
    - تحليل الاستجابات JSON
    - إدارة الأخطاء
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        system_prompt_path: Optional[str] = None
    ):
        """
        تهيئة العميل
        
        Args:
            api_key: مفتاح API (أو من متغير البيئة GEMINI_API_KEY)
            model: اسم النموذج
            system_prompt_path: مسار ملف البرومبت
        """
        if genai is None:
            raise ImportError(
                "google-generativeai is required. "
                "Install with: pip install google-generativeai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model_name = model
        self.system_prompt = self._load_system_prompt(system_prompt_path)
        
        # تهيئة Gemini
        genai.configure(api_key=self.api_key)
        
        # إعدادات التوليد
        self.generation_config = genai.GenerationConfig(
            temperature=0.1,  # منخفض للدقة
            max_output_tokens=2048,
            response_mime_type="application/json"
        )
        
        # إعدادات الأمان
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # إنشاء النموذج
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )
        
        # تاريخ المحادثة
        self.chat_session = None
        self._conversation_history: List[Dict[str, str]] = []
    
    def _load_system_prompt(self, path: Optional[str] = None) -> str:
        """تحميل System Prompt من ملف"""
        if path is None:
            # المسار الافتراضي
            default_path = Path(__file__).parent.parent.parent / "config" / "system_prompt.txt"
            path = str(default_path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # برومبت افتراضي مختصر
            return """
            أنت AI System Agent لـ Raspberry Pi OS.
            رد دائماً بصيغة JSON فقط.
            لا تقترح أوامر خطرة.
            """
    
    def start_conversation(self) -> None:
        """بدء محادثة جديدة"""
        self.chat_session = self.model.start_chat(history=[])
        self._conversation_history = []
    
    def _build_context_message(
        self,
        user_request: str,
        system_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        بناء رسالة تحتوي على السياق والطلب
        
        Args:
            user_request: طلب المستخدم
            system_context: سياق النظام (معلومات، سجلات، الخ)
        
        Returns:
            رسالة مُهيكلة
        """
        message_parts = []
        
        # إضافة سياق النظام إن وُجد
        if system_context:
            message_parts.append("=== SYSTEM CONTEXT ===")
            message_parts.append(json.dumps(system_context, indent=2, ensure_ascii=False))
            message_parts.append("=== END CONTEXT ===\n")
        
        # إضافة الطلب
        message_parts.append("=== USER REQUEST ===")
        message_parts.append(user_request)
        message_parts.append("=== END REQUEST ===")
        
        # تذكير بصيغة JSON
        message_parts.append("\nRespond with valid JSON only.")
        
        return "\n".join(message_parts)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        تحليل استجابة Gemini إلى JSON
        
        Args:
            response_text: نص الاستجابة
        
        Returns:
            قاموس Python
        """
        # تنظيف النص
        text = response_text.strip()
        
        # إزالة علامات markdown إن وجدت
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # محاولة إصلاح JSON المكسور
            return {
                "intent": "parse_error",
                "category": "error",
                "risk": "low",
                "diagnosis": f"Failed to parse AI response: {str(e)}",
                "plan": [],
                "commands_proposed": [],
                "execution_mode": "blocked",
                "security_note": "Response was not valid JSON",
                "raw_response": response_text[:500]
            }
    
    async def analyze_async(
        self,
        user_request: str,
        system_context: Optional[Dict[str, Any]] = None,
        use_conversation: bool = True
    ) -> GeminiResponse:
        """
        تحليل طلب بشكل غير متزامن
        
        Args:
            user_request: طلب المستخدم
            system_context: سياق النظام
            use_conversation: استخدام سياق المحادثة السابقة
        
        Returns:
            GeminiResponse
        """
        try:
            message = self._build_context_message(user_request, system_context)
            
            if use_conversation:
                if self.chat_session is None:
                    self.start_conversation()
                
                response = await asyncio.to_thread(
                    self.chat_session.send_message,
                    message
                )
            else:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    message
                )
            
            # استخراج النص
            response_text = response.text
            
            # تحليل JSON
            parsed_data = self._parse_response(response_text)
            
            # حفظ في التاريخ
            self._conversation_history.append({
                "role": "user",
                "content": user_request
            })
            self._conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            return GeminiResponse(
                success=True,
                data=parsed_data,
                raw_response=response_text
            )
            
        except Exception as e:
            return GeminiResponse(
                success=False,
                error=str(e)
            )
    
    def analyze(
        self,
        user_request: str,
        system_context: Optional[Dict[str, Any]] = None,
        use_conversation: bool = True
    ) -> GeminiResponse:
        """
        تحليل طلب بشكل متزامن
        
        Args:
            user_request: طلب المستخدم
            system_context: سياق النظام
            use_conversation: استخدام سياق المحادثة السابقة
        
        Returns:
            GeminiResponse
        """
        try:
            message = self._build_context_message(user_request, system_context)
            
            if use_conversation:
                if self.chat_session is None:
                    self.start_conversation()
                
                response = self.chat_session.send_message(message)
            else:
                response = self.model.generate_content(message)
            
            # استخراج النص
            response_text = response.text
            
            # تحليل JSON
            parsed_data = self._parse_response(response_text)
            
            # حفظ في التاريخ
            self._conversation_history.append({
                "role": "user",
                "content": user_request
            })
            self._conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            return GeminiResponse(
                success=True,
                data=parsed_data,
                raw_response=response_text
            )
            
        except Exception as e:
            return GeminiResponse(
                success=False,
                error=str(e)
            )
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """الحصول على تاريخ المحادثة"""
        return self._conversation_history.copy()
    
    def clear_conversation(self) -> None:
        """مسح تاريخ المحادثة"""
        self.chat_session = None
        self._conversation_history = []


# للاختبار المباشر
if __name__ == "__main__":
    # اختبار بسيط
    try:
        client = GeminiClient()
        response = client.analyze(
            user_request="ما هي حالة الذاكرة؟",
            system_context={
                "hostname": "raspberrypi",
                "memory": {"total": "4GB", "used": "2.1GB", "free": "1.9GB"}
            }
        )
        
        if response.success:
            print("✅ Success!")
            print(json.dumps(response.data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.error}")
            
    except Exception as e:
        print(f"❌ Setup Error: {e}")
