"""
EdgeMind Agent - Gemini API Client
===================================
Official client for communicating with Gemini API
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
    """Structured Gemini response"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None


class GeminiClient:
    """
    Gemini API Client for EdgeMind Agent
    
    Handles:
    - Connection setup
    - Sending context and requests
    - Parsing JSON responses
    - Error management
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        system_prompt_path: Optional[str] = None
    ):
        """
        Initialize the client
        
        Args:
            api_key: API key (or from GEMINI_API_KEY environment variable)
            model: Model name
            system_prompt_path: Path to system prompt file
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
        
        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        
        # Generation settings
        self.generation_config = genai.GenerationConfig(
            temperature=0.1,  # Low for precision
            max_output_tokens=2048,
            response_mime_type="application/json"
        )
        
        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Create model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )
        
        # Conversation history
        self.chat_session = None
        self._conversation_history: List[Dict[str, str]] = []
    
    def _load_system_prompt(self, path: Optional[str] = None) -> str:
        """Load System Prompt from file"""
        if path is None:
            # Default path
            default_path = Path(__file__).parent.parent.parent / "config" / "system_prompt.txt"
            path = str(default_path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Default short prompt
            return """
            You are an AI System Agent for Raspberry Pi OS.
            Always respond in JSON format only.
            Do not suggest dangerous commands.
            """
    
    def start_conversation(self) -> None:
        """Start a new conversation"""
        self.chat_session = self.model.start_chat(history=[])
        self._conversation_history = []
    
    def _build_context_message(
        self,
        user_request: str,
        system_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a message containing context and request
        
        Args:
            user_request: User request
            system_context: System context (info, logs, etc.)
        
        Returns:
            Structured message
        """
        message_parts = []
        
        # Add system context if available
        if system_context:
            message_parts.append("=== SYSTEM CONTEXT ===")
            message_parts.append(json.dumps(system_context, indent=2, ensure_ascii=False))
            message_parts.append("=== END CONTEXT ===\n")
        
        # Add request
        message_parts.append("=== USER REQUEST ===")
        message_parts.append(user_request)
        message_parts.append("=== END REQUEST ===")
        
        # Reminder for JSON format
        message_parts.append("\nRespond with valid JSON only.")
        
        return "\n".join(message_parts)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response to JSON
        
        Args:
            response_text: Response text
        
        Returns:
            Python dictionary
        """
        # Clean text
        text = response_text.strip()
        
        # Remove markdown markers if present
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
            # Attempt to fix broken JSON
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
        Analyze request asynchronously
        
        Args:
            user_request: User request
            system_context: System context
            use_conversation: Use previous conversation context
        
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
            
            # Extract text
            response_text = response.text
            
            # Parse JSON
            parsed_data = self._parse_response(response_text)
            
            # Save in history
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
        Analyze request synchronously
        
        Args:
            user_request: User request
            system_context: System context
            use_conversation: Use previous conversation context
        
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
            
            # Extract text
            response_text = response.text
            
            # Parse JSON
            parsed_data = self._parse_response(response_text)
            
            # Save in history
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
        """Get conversation history"""
        return self._conversation_history.copy()
    
    def clear_conversation(self) -> None:
        """Clear conversation history"""
        self.chat_session = None
        self._conversation_history = []


# For direct testing
if __name__ == "__main__":
    # Simple test
    try:
        client = GeminiClient()
        response = client.analyze(
            user_request="What is the memory status?",
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
