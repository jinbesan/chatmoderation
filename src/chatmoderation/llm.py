from openai import OpenAI
from typing import Optional, Dict, Any, List
import json


class LLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "nvidia/nemotron-3-super-120b-a12b:free",
        default_temperature: float = 0.3,
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.default_temperature = default_temperature

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        temp = temperature if temperature is not None else self.default_temperature

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
        }

        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM Error] {type(e).__name__}: {e}")
            return None

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        response = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        if response is None:
            return {"severity": "Medium", "confidence": 50, "intervention_needed": True, "reasoning": "Fallback due to LLM error"}
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"severity": "Medium", "confidence": 50, "intervention_needed": True, "reasoning": "Fallback due to JSON parse error"}

    def chat_str(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> str:
        return self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )


def create_client(
    api_key: str,
    model: str = "nvidia/nemotron-3-super-120b-a12b:free",
) -> LLMClient:
    return LLMClient(api_key=api_key, model=model)