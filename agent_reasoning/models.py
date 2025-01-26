"""Module for handling different LLM APIs and model types."""

from enum import Enum, auto
import os
from typing import Dict, List, Optional

from openai import OpenAI
from google import genai
from ollama import generate


class ModelType(Enum):
    """Enum for different types of models supported by the evaluator."""
    OPENAI = auto()
    GEMINI = auto()
    OLLAMA = auto()


class ModelClient:
    """Client for handling different model APIs."""
    
    def __init__(self, model: str):
        """Initialize model client.
        
        Args:
            model: Name of the model to use
            
        Raises:
            ValueError: If model type is unknown
        """
        self.model = model
        self.openai_client: Optional[OpenAI] = None
        self.gemini_client: Optional[genai.Client] = None
        
        # Initialize the appropriate client based on model type
        if self.model.startswith(('gpt-', 'o1-')):
            self.model_type = ModelType.OPENAI
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
        elif self.model.startswith('gemini-'):
            self.model_type = ModelType.GEMINI
            self.gemini_client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY"),
                http_options={'api_version': 'v1alpha'}
            )
            
        elif self.model.startswith('deepseek-'):
            self.model_type = ModelType.OLLAMA  # Deepseek models use Ollama
            
        else:
            raise ValueError(f"Unknown model: {self.model}")

    def generate(self, messages: List[Dict[str, str]]) -> str:
        """Generate response from the model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Generated response text
            
        Raises:
            ValueError: If response is empty or invalid
        """
        if self.model_type == ModelType.OPENAI:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
                
            chat_completion = self.openai_client.chat.completions.create(
                messages=[{
                    "role": msg["role"],
                    "content": msg["content"]
                } for msg in messages],
                model=self.model,
            )
            response_content = chat_completion.choices[0].message.content
            if response_content is None:
                raise ValueError("Received empty response from OpenAI")
            return response_content
        
        elif self.model_type == ModelType.GEMINI:
            if not self.gemini_client:
                raise ValueError("Gemini client not initialized")
                
            config = {'thinking_config': {'include_thoughts': True}}
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=messages[-1]["content"],
                config=config
            )
            
            # Extract the actual response text (excluding thoughts)
            response_text = ""
            is_thinking = False
            started_thinking = False
            for part in response.candidates[0].content.parts:
                if part.thought:
                    is_thinking = True
                    if not started_thinking:
                        started_thinking = True
                        response_text += "<thinking>\n"
                    response_text += part.text or ""
                else:
                    if is_thinking:
                        response_text += "\n</thinking>\n\n"
                        is_thinking = False
                    response_text += part.text or ""
                    
            return response_text
        
        else:  # Ollama models
            # Model name mappings
            OLLAMA_MODEL_MAP = {
                "deepseek-r1-distill-llama-8b": "hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q8_0"
            }
            
            ollama_model = OLLAMA_MODEL_MAP.get(self.model, self.model)
            response = generate(
                model=ollama_model,
                prompt=messages[-1]["content"]
            )
            return response.response 