"""
EdgeMind Agent - Main Agent
============================
Main system brain
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .context_builder import ContextBuilder, SystemContext
from .decision_engine import DecisionEngine, Decision, RiskLevel, ExecutionMode
from ..api.gemini_client import GeminiClient, GeminiResponse
from ..gateway.security_gateway import SecurityGateway, ExecutionResult


@dataclass
class AgentResponse:
    """Complete Agent response"""
    success: bool
    decision: Optional[Decision] = None
    execution_results: Optional[List[ExecutionResult]] = None
    error: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "decision": self.decision.to_dict() if self.decision else None,
            "execution_results": [r.to_dict() for r in self.execution_results] if self.execution_results else None,
            "error": self.error,
            "timestamp": self.timestamp
        }


class EdgeMindAgent:
    """
    EdgeMind Agent - Main Brain
    
    Integrates:
    - Context collection (ContextBuilder)
    - Intelligent analysis (GeminiClient)
    - Decision making (DecisionEngine)
    - Secure execution (SecurityGateway)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
        strict_mode: bool = True,
        auto_execute: bool = False
    ):
        """
        Initialize Agent
        
        Args:
            api_key: Gemini API key
            config_path: Settings file path
            strict_mode: Strict security mode
            auto_execute: Auto-execute low-risk commands
        """
        self.strict_mode = strict_mode
        self.auto_execute = auto_execute
        
        # Load settings
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.context_builder = ContextBuilder(
            max_log_lines=self.config.get("context", {}).get("max_log_lines", 50)
        )
        
        self.gemini_client = GeminiClient(
            api_key=api_key,
            model=self.config.get("gemini", {}).get("model", "gemini-1.5-pro")
        )
        
        self.decision_engine = DecisionEngine(strict_mode=strict_mode)
        
        # Determine whitelist path
        if config_path:
            whitelist_path = Path(config_path).parent / "whitelist.yaml"
        else:
            whitelist_path = Path(__file__).parent.parent.parent / "config" / "whitelist.yaml"
        
        self.security_gateway = SecurityGateway(
            whitelist_path=str(whitelist_path),
            strict_mode=strict_mode
        )
        
        # Session history
        self._session_history: List[AgentResponse] = []
        self._session_start = datetime.now()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load settings"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}
    
    def _build_context(
        self,
        include_full: bool = True,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build context for sending to AI
        
        Args:
            include_full: Include full context
            custom_data: Additional data
        
        Returns:
            Structured context
        """
        if include_full:
            context = self.context_builder.build(custom_data=custom_data)
            return context.to_dict()
        else:
            return self.context_builder.build_minimal()
    
    async def process_async(
        self,
        user_request: str,
        include_context: bool = True,
        execute_commands: Optional[bool] = None,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process request asynchronously
        
        Args:
            user_request: User request
            include_context: Include system context
            execute_commands: Execute commands (None = use settings)
            custom_context: Custom context
        
        Returns:
            AgentResponse
        """
        try:
            # Build context
            context = None
            if include_context:
                context = self._build_context(custom_data=custom_context)
            elif custom_context:
                context = custom_context
            
            # Send to Gemini
            gemini_response = await self.gemini_client.analyze_async(
                user_request=user_request,
                system_context=context
            )
            
            if not gemini_response.success:
                return AgentResponse(
                    success=False,
                    error=gemini_response.error
                )
            
            # Analyze the response
            decision = self.decision_engine.process_ai_response(
                gemini_response.data
            )
            
            # Execute commands if requested
            execution_results = None
            should_execute = execute_commands if execute_commands is not None else self.auto_execute
            
            if should_execute and decision.is_executable():
                if decision.risk == RiskLevel.LOW or (
                    decision.risk == RiskLevel.MEDIUM and 
                    not decision.requires_confirmation()
                ):
                    execution_results = []
                    for cmd in decision.commands_proposed:
                        result = self.security_gateway.execute(cmd)
                        execution_results.append(result)
            
            response = AgentResponse(
                success=True,
                decision=decision,
                execution_results=execution_results
            )
            
            self._session_history.append(response)
            return response
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    def process(
        self,
        user_request: str,
        include_context: bool = True,
        execute_commands: Optional[bool] = None,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process request synchronously
        
        Args:
            user_request: User request
            include_context: Include system context
            execute_commands: Execute commands (None = use settings)
            custom_context: Custom context
        
        Returns:
            AgentResponse
        """
        try:
            # Build context
            context = None
            if include_context:
                context = self._build_context(custom_data=custom_context)
            elif custom_context:
                context = custom_context
            
            # Send to Gemini
            gemini_response = self.gemini_client.analyze(
                user_request=user_request,
                system_context=context
            )
            
            if not gemini_response.success:
                return AgentResponse(
                    success=False,
                    error=gemini_response.error
                )
            
            # Analyze the response
            decision = self.decision_engine.process_ai_response(
                gemini_response.data
            )
            
            # Execute commands if requested
            execution_results = None
            should_execute = execute_commands if execute_commands is not None else self.auto_execute
            
            if should_execute and decision.is_executable():
                if decision.risk == RiskLevel.LOW or (
                    decision.risk == RiskLevel.MEDIUM and 
                    not decision.requires_confirmation()
                ):
                    execution_results = []
                    for cmd in decision.commands_proposed:
                        result = self.security_gateway.execute(cmd)
                        execution_results.append(result)
            
            response = AgentResponse(
                success=True,
                decision=decision,
                execution_results=execution_results
            )
            
            self._session_history.append(response)
            return response
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    def execute_decision(
        self,
        decision: Decision,
        confirm: bool = False
    ) -> List[ExecutionResult]:
        """
        Execute decision
        
        Args:
            decision: Decision to execute
            confirm: Confirm execution for medium-risk commands
        
        Returns:
            List of execution results
        """
        results = []
        
        if not decision.is_executable():
            return results
        
        if decision.requires_confirmation() and not confirm:
            return results
        
        for cmd in decision.commands_proposed:
            result = self.security_gateway.execute(cmd)
            results.append(result)
        
        return results
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get session history"""
        return [r.to_dict() for r in self._session_history]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Session statistics"""
        total = len(self._session_history)
        successful = sum(1 for r in self._session_history if r.success)
        
        return {
            "session_start": self._session_start.isoformat(),
            "total_requests": total,
            "successful": successful,
            "failed": total - successful,
            "duration_minutes": (datetime.now() - self._session_start).total_seconds() / 60
        }
    
    def clear_session(self) -> None:
        """Clear session"""
        self._session_history = []
        self._session_start = datetime.now()
        self.gemini_client.clear_conversation()


# For testing
if __name__ == "__main__":
    print("EdgeMind Agent - Test Mode")
    print("Set GEMINI_API_KEY environment variable to test")
