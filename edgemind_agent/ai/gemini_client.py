"""Gemini AI client for analysis and planning."""

import os
import logging
from typing import Dict, Any, Optional, List
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


logger = logging.getLogger(__name__)


class GeminiAIBrain:
    """AI brain using Gemini API for system analysis and planning."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro"):
        """Initialize the Gemini AI client.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
            model_name: Name of the Gemini model to use.
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package is not installed. "
                "Install it with: pip install google-generativeai"
            )
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Initialized Gemini AI Brain with model: {model_name}")

    def analyze_system_state(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system state and identify issues.
        
        Args:
            context: System context collected by the context collector.
            
        Returns:
            Analysis results including identified issues and recommendations.
        """
        try:
            # Prepare the context for the AI
            context_str = json.dumps(context, indent=2, default=str)
            
            prompt = f"""You are EdgeMind Agent, an AI system analyst for Raspberry Pi OS.
Analyze the following system context and provide insights:

SYSTEM CONTEXT:
{context_str}

Please provide:
1. A brief summary of the system health (1-2 sentences)
2. Any issues or anomalies detected
3. Severity of each issue (LOW, MEDIUM, HIGH, CRITICAL)
4. Recommendations for addressing each issue

IMPORTANT: You are an analysis and planning assistant only. You CANNOT execute commands.
Your output will be reviewed by a security layer before any action is taken.

Respond in JSON format with the following structure:
{{
  "summary": "brief health summary",
  "issues": [
    {{
      "description": "issue description",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "category": "memory|cpu|disk|network|service|security|other"
    }}
  ],
  "recommendations": [
    {{
      "issue": "related issue",
      "action": "recommended action description",
      "priority": "LOW|MEDIUM|HIGH|CRITICAL"
    }}
  ]
}}
"""
            
            response = self.model.generate_content(prompt)
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            
            analysis = json.loads(response_text)
            
            logger.info("System analysis completed successfully")
            return {
                'status': 'success',
                'analysis': analysis,
                'raw_response': response.text
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                'status': 'error',
                'error': 'Failed to parse AI response',
                'raw_response': response.text if 'response' in locals() else None
            }
        except Exception as e:
            logger.error(f"Error during system analysis: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def plan_actions(self, analysis: Dict[str, Any], 
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan safe actions based on analysis results.
        
        Args:
            analysis: Analysis results from analyze_system_state.
            context: Original system context.
            
        Returns:
            Planned actions with safety considerations.
        """
        try:
            analysis_str = json.dumps(analysis, indent=2, default=str)
            
            prompt = f"""You are EdgeMind Agent, an AI system planner for Raspberry Pi OS.
Based on the following analysis, create a safe action plan:

ANALYSIS:
{analysis_str}

Create a detailed action plan that:
1. Addresses the most critical issues first
2. Specifies EXACT commands that could help (these will be validated by security layer)
3. Includes verification steps
4. Considers dependencies between actions

IMPORTANT CONSTRAINTS:
- You CANNOT execute commands yourself
- All suggested commands will be validated against a whitelist
- Destructive operations (rm -rf, dd, etc.) are FORBIDDEN
- Focus on safe diagnostic and remediation commands only

Respond in JSON format:
{{
  "plan": [
    {{
      "step": 1,
      "description": "what this step does",
      "commands": ["exact", "commands", "to", "run"],
      "reasoning": "why this step is needed",
      "risks": "potential risks",
      "verification": "how to verify success"
    }}
  ],
  "overall_risk": "LOW|MEDIUM|HIGH",
  "requires_approval": true|false
}}
"""
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            
            plan = json.loads(response_text)
            
            logger.info("Action plan created successfully")
            return {
                'status': 'success',
                'plan': plan,
                'raw_response': response.text
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                'status': 'error',
                'error': 'Failed to parse AI response',
                'raw_response': response.text if 'response' in locals() else None
            }
        except Exception as e:
            logger.error(f"Error during action planning: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information.
        """
        return {
            'model_name': self.model_name,
            'api_available': GEMINI_AVAILABLE
        }
