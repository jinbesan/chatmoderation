from groq import Groq
from typing import Optional, Dict, Any, List
import json


class LLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.groq.com",
        model: str = "llama-3.1-8b-instant",
        default_temperature: float = 0.5,
    ):
        self.client = Groq(
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
        
        if debug := True: # Set to True to enable debug logging of prompts and responses
            # try:
            #     print(f"[DEBUG] User prompt: {user_prompt}")
            # except UnicodeEncodeError:
            #     print("[DEBUG] User prompt: [Unicode content - unable to display]")


            try:
                print(f"[DEBUG] Raw response: {response}")
            except UnicodeEncodeError:
                print("[DEBUG] Raw response: [Unicode content - unable to display]")
            except Exception:
                print("[DEBUG] Raw response: [Error displaying response]")
                
        if response is None:
            return {"severity": "Medium", "confidence": 50, "intervention_needed": True, "trajectory": "stable", "signals_detected": [], "reasoning": "Fallback due to LLM error"}
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"severity": "Medium", "confidence": 50, "intervention_needed": True, "trajectory": "stable", "signals_detected": [], "reasoning": "Fallback due to JSON parse error"}

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
    base_url: str = "https://api.groq.com",
    model: str = "llama-3.1-8b-instant",
) -> LLMClient:
    return LLMClient(api_key=api_key, base_url=base_url, model=model)