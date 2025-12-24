#!/usr/bin/env python3
"""
C.O.R.A Ollama HTTP API Wrapper
Direct HTTP communication with Ollama (replaces subprocess.run)

Per ARCHITECTURE.md v2.0.0:
- HTTP API at localhost:11434
- Streaming responses
- Model management
- Context window handling
"""

import json
import asyncio
import requests
import aiohttp
from typing import Optional, Dict, Any, Generator, List, AsyncGenerator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


# Ollama API Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_TIMEOUT = 120  # seconds


@dataclass
class OllamaResponse:
    """Structured response from Ollama API."""
    content: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    error: Optional[str] = None


def check_ollama() -> Dict[str, Any]:
    """Check if Ollama is running and get status.

    Returns:
        Dict with 'connected', 'version', 'models' keys
    """
    try:
        # Check API endpoint
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get('models', [])
            return {
                'connected': True,
                'models': len(models),
                'model_names': [m.get('name', '') for m in models],
                'error': None
            }
    except requests.ConnectionError:
        return {
            'connected': False,
            'models': 0,
            'model_names': [],
            'error': 'Ollama not running. Start with: ollama serve'
        }
    except requests.Timeout:
        return {
            'connected': False,
            'models': 0,
            'model_names': [],
            'error': 'Ollama connection timeout'
        }
    except Exception as e:
        return {
            'connected': False,
            'models': 0,
            'model_names': [],
            'error': str(e)
        }


def list_models() -> List[Dict[str, Any]]:
    """List all available Ollama models.

    Returns:
        List of model info dicts with 'name', 'size', 'modified' keys
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            models = []
            for m in data.get('models', []):
                models.append({
                    'name': m.get('name', ''),
                    'size': m.get('size', 0),
                    'modified': m.get('modified_at', ''),
                    'digest': m.get('digest', '')[:12]
                })
            return models
    except Exception:
        pass
    return []


def pull_model(model_name: str, callback: Optional[callable] = None) -> bool:
    """Pull/download a model from Ollama library.

    Args:
        model_name: Name of model to pull (e.g., 'llama3.2:3b')
        callback: Optional callback for progress updates

    Returns:
        True if successful
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={'name': model_name},
            stream=True,
            timeout=600  # 10 min for large models
        )

        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if callback:
                    status = data.get('status', '')
                    completed = data.get('completed', 0)
                    total = data.get('total', 0)
                    callback(status, completed, total)

                if data.get('status') == 'success':
                    return True

        return resp.status_code == 200
    except Exception as e:
        if callback:
            callback(f'Error: {e}', 0, 0)
        return False


def chat(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> OllamaResponse:
    """Send a chat completion request (non-streaming).

    Args:
        messages: List of {'role': 'user'|'assistant', 'content': '...'}
        model: Model name
        system: Optional system prompt
        temperature: Sampling temperature (0-1)
        max_tokens: Max response tokens
        timeout: Request timeout in seconds

    Returns:
        OllamaResponse with content and metadata
    """
    try:
        payload = {
            'model': model,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['messages'] = [{'role': 'system', 'content': system}] + messages

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=timeout
        )

        if resp.status_code == 200:
            data = resp.json()
            message = data.get('message', {})
            return OllamaResponse(
                content=message.get('content', ''),
                model=data.get('model', model),
                done=data.get('done', True),
                total_duration=data.get('total_duration'),
                load_duration=data.get('load_duration'),
                prompt_eval_count=data.get('prompt_eval_count'),
                eval_count=data.get('eval_count')
            )
        else:
            return OllamaResponse(
                content='',
                model=model,
                done=True,
                error=f"HTTP {resp.status_code}: {resp.text}"
            )

    except requests.ConnectionError:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Ollama not running. Start with: ollama serve'
        )
    except requests.Timeout:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Request timeout - model may be loading'
        )
    except Exception as e:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error=str(e)
        )


def chat_stream(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Generator[str, None, None]:
    """Send a streaming chat completion request.

    Args:
        messages: List of {'role': 'user'|'assistant', 'content': '...'}
        model: Model name
        system: Optional system prompt
        temperature: Sampling temperature (0-1)
        max_tokens: Max response tokens
        timeout: Request timeout in seconds

    Yields:
        Response tokens as they arrive
    """
    try:
        payload = {
            'model': model,
            'messages': messages,
            'stream': True,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['messages'] = [{'role': 'system', 'content': system}] + messages

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            stream=True,
            timeout=timeout
        )

        if resp.status_code == 200:
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    message = data.get('message', {})
                    content = message.get('content', '')
                    if content:
                        yield content
                    if data.get('done', False):
                        break
        else:
            yield f"[Error: HTTP {resp.status_code}]"

    except requests.ConnectionError:
        yield "[Error: Ollama not running]"
    except requests.Timeout:
        yield "[Error: Request timeout]"
    except Exception as e:
        yield f"[Error: {e}]"


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    raw: bool = False,
    timeout: int = DEFAULT_TIMEOUT
) -> OllamaResponse:
    """Generate completion for a single prompt (non-chat).

    Args:
        prompt: The prompt text
        model: Model name
        system: Optional system prompt
        temperature: Sampling temperature
        max_tokens: Max response tokens
        raw: If True, no formatting applied
        timeout: Request timeout

    Returns:
        OllamaResponse with content and metadata
    """
    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'raw': raw,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['system'] = system

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=timeout
        )

        if resp.status_code == 200:
            data = resp.json()
            return OllamaResponse(
                content=data.get('response', ''),
                model=data.get('model', model),
                done=data.get('done', True),
                total_duration=data.get('total_duration'),
                load_duration=data.get('load_duration'),
                prompt_eval_count=data.get('prompt_eval_count'),
                eval_count=data.get('eval_count')
            )
        else:
            return OllamaResponse(
                content='',
                model=model,
                done=True,
                error=f"HTTP {resp.status_code}: {resp.text}"
            )

    except requests.ConnectionError:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Ollama not running'
        )
    except Exception as e:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error=str(e)
        )


def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a model.

    Args:
        model_name: Name of the model

    Returns:
        Dict with model details or None
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/show",
            json={'name': model_name},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def delete_model(model_name: str) -> bool:
    """Delete a model from Ollama.

    Args:
        model_name: Name of model to delete

    Returns:
        True if successful
    """
    try:
        resp = requests.delete(
            f"{OLLAMA_BASE_URL}/api/delete",
            json={'name': model_name},
            timeout=30
        )
        return resp.status_code == 200
    except Exception:
        return False


def create_model(
    name: str,
    modelfile: str,
    callback: Optional[callable] = None
) -> bool:
    """Create a custom model from a Modelfile.

    Args:
        name: Name for the new model
        modelfile: Modelfile content
        callback: Optional progress callback

    Returns:
        True if successful
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/create",
            json={'name': name, 'modelfile': modelfile},
            stream=True,
            timeout=300
        )

        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if callback:
                    callback(data.get('status', ''))
                if data.get('status') == 'success':
                    return True

        return resp.status_code == 200
    except Exception:
        return False


# ============ VISION (Image Analysis) ============
# Per ARCHITECTURE.md v2.4.0 - Vision analysis using llava

VISION_MODEL = "llava"  # Multimodal vision model


def generate_with_image(
    prompt: str,
    image_path: str,
    model: str = VISION_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 150,
    timeout: int = 60
) -> OllamaResponse:
    """Generate response based on an image using vision model (llava).

    Args:
        prompt: Question about the image
        image_path: Path to the image file
        model: Vision model to use (default: llava)
        temperature: Sampling temperature
        max_tokens: Max response tokens
        timeout: Request timeout

    Returns:
        OllamaResponse with description of the image
    """
    import base64
    from pathlib import Path

    try:
        # Read and encode the image
        img_path = Path(image_path)
        if not img_path.exists():
            return OllamaResponse(
                content='',
                model=model,
                done=True,
                error=f"Image not found: {image_path}"
            )

        with open(img_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Build payload with image
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [image_data]
                }
            ],
            'stream': False,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens
            }
        }

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=timeout
        )

        if resp.status_code == 200:
            data = resp.json()
            message = data.get('message', {})
            return OllamaResponse(
                content=message.get('content', ''),
                model=data.get('model', model),
                done=data.get('done', True),
                total_duration=data.get('total_duration'),
                eval_count=data.get('eval_count')
            )
        else:
            return OllamaResponse(
                content='',
                model=model,
                done=True,
                error=f"HTTP {resp.status_code}: {resp.text}"
            )

    except requests.ConnectionError:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Ollama not running'
        )
    except Exception as e:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error=str(e)
        )


# Convenience functions for CORA integration

def quick_ask(question: str, model: str = DEFAULT_MODEL) -> str:
    """Quick single-turn question (convenience wrapper).

    Args:
        question: The question to ask
        model: Model to use

    Returns:
        Response text or error message
    """
    response = chat(
        messages=[{'role': 'user', 'content': question}],
        model=model
    )
    if response.error:
        return f"[Error: {response.error}]"
    return response.content


def summarize(text: str, model: str = DEFAULT_MODEL) -> str:
    """Summarize text (convenience wrapper).

    Args:
        text: Text to summarize
        model: Model to use

    Returns:
        Summary text
    """
    return quick_ask(
        f"Summarize this concisely:\n\n{text}",
        model=model
    )


# ============ THINK (Quick Local AI) ============
# Per ARCHITECTURE.md v2.2.0 - Fast local AI for internal decisions

THINK_MODEL = "dolphin-mistral:7b"  # Small, fast, uncensored model


def think(
    prompt: str,
    model: str = THINK_MODEL,
    max_tokens: int = 100,
    temperature: float = 0.3,
    timeout: int = 30
) -> str:
    """Quick local AI for simple tasks - FREE, Fast, Fallback.

    Per ARCHITECTURE.md Section: Ollama Think (Quick Local AI)

    Use this for:
    - Quick lookups and categorization
    - Simple yes/no decisions
    - Internal processing (not user-facing responses)
    - Summarization of internal data
    - Fallback when main AI is busy

    Args:
        prompt: The question/prompt
        model: Model to use (default: dolphin-mistral:7b for speed)
        max_tokens: Max response tokens (keep small for speed)
        temperature: Low temperature for consistent results
        timeout: Short timeout for quick responses

    Returns:
        Response text or empty string on error
    """
    try:
        response = generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
        if response.error:
            return ""
        return response.content.strip()
    except Exception:
        return ""


def think_bool(prompt: str, model: str = THINK_MODEL) -> bool:
    """Quick yes/no decision using local AI.

    Args:
        prompt: Question expecting yes/no answer

    Returns:
        True for yes/affirmative, False otherwise
    """
    response = think(
        f"Answer only 'yes' or 'no': {prompt}",
        model=model,
        max_tokens=10
    ).lower()
    return response.startswith('yes') or 'true' in response


def think_choice(
    prompt: str,
    choices: list,
    model: str = THINK_MODEL
) -> str:
    """Quick multiple choice decision using local AI.

    Args:
        prompt: The question
        choices: List of valid choices

    Returns:
        The chosen option or first choice on error
    """
    choice_str = ', '.join(choices)
    response = think(
        f"{prompt}\nChoose ONLY ONE from: {choice_str}\nAnswer with just the choice:",
        model=model,
        max_tokens=20
    ).strip().lower()

    # Find matching choice
    for choice in choices:
        if choice.lower() in response or response in choice.lower():
            return choice

    return choices[0] if choices else ""


def think_classify(
    text: str,
    categories: list,
    model: str = THINK_MODEL
) -> str:
    """Classify text into one of the categories.

    Args:
        text: Text to classify
        categories: List of category names

    Returns:
        Matching category
    """
    return think_choice(
        f"Classify this text: '{text}'",
        categories,
        model=model
    )


def think_extract(
    text: str,
    what: str,
    model: str = THINK_MODEL
) -> str:
    """Extract specific information from text.

    Args:
        text: Source text
        what: What to extract (e.g., "email address", "date", "name")

    Returns:
        Extracted value or empty string
    """
    return think(
        f"Extract the {what} from this text. Return ONLY the {what}, nothing else:\n{text}",
        model=model,
        max_tokens=50
    )


async def async_think(
    prompt: str,
    model: str = THINK_MODEL,
    max_tokens: int = 100,
    temperature: float = 0.3,
    timeout: int = 30
) -> str:
    """Async version of think() for non-blocking quick AI.

    Args:
        prompt: The question/prompt
        model: Model to use
        max_tokens: Max response tokens
        temperature: Sampling temperature
        timeout: Request timeout

    Returns:
        Response text or empty string on error
    """
    try:
        response = await async_generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
        if response.error:
            return ""
        return response.content.strip()
    except Exception:
        return ""


# ============ ASYNC VERSIONS ============
# Non-blocking async functions for GUI/event loop integration

# Thread pool for running sync requests in async context
_executor = ThreadPoolExecutor(max_workers=3)


async def async_check_ollama() -> Dict[str, Any]:
    """Async version of check_ollama()."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, check_ollama)


async def async_list_models() -> List[Dict[str, Any]]:
    """Async version of list_models()."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, list_models)


async def async_chat(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> OllamaResponse:
    """Async non-blocking chat completion using aiohttp.

    Args:
        messages: List of {'role': 'user'|'assistant', 'content': '...'}
        model: Model name
        system: Optional system prompt
        temperature: Sampling temperature (0-1)
        max_tokens: Max response tokens
        timeout: Request timeout in seconds

    Returns:
        OllamaResponse with content and metadata
    """
    try:
        payload = {
            'model': model,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['messages'] = [{'role': 'system', 'content': system}] + messages

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    message = data.get('message', {})
                    return OllamaResponse(
                        content=message.get('content', ''),
                        model=data.get('model', model),
                        done=data.get('done', True),
                        total_duration=data.get('total_duration'),
                        load_duration=data.get('load_duration'),
                        prompt_eval_count=data.get('prompt_eval_count'),
                        eval_count=data.get('eval_count')
                    )
                else:
                    text = await resp.text()
                    return OllamaResponse(
                        content='',
                        model=model,
                        done=True,
                        error=f"HTTP {resp.status}: {text}"
                    )

    except aiohttp.ClientConnectorError:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Ollama not running. Start with: ollama serve'
        )
    except asyncio.TimeoutError:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Request timeout - model may be loading'
        )
    except Exception as e:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error=str(e)
        )


async def async_chat_stream(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> AsyncGenerator[str, None]:
    """Async streaming chat completion.

    Args:
        messages: List of {'role': 'user'|'assistant', 'content': '...'}
        model: Model name
        system: Optional system prompt
        temperature: Sampling temperature (0-1)
        max_tokens: Max response tokens
        timeout: Request timeout in seconds

    Yields:
        Response tokens as they arrive
    """
    try:
        payload = {
            'model': model,
            'messages': messages,
            'stream': True,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['messages'] = [{'role': 'system', 'content': system}] + messages

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    async for line in resp.content:
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            message = data.get('message', {})
                            content = message.get('content', '')
                            if content:
                                yield content
                            if data.get('done', False):
                                break
                else:
                    yield f"[Error: HTTP {resp.status}]"

    except aiohttp.ClientConnectorError:
        yield "[Error: Ollama not running]"
    except asyncio.TimeoutError:
        yield "[Error: Request timeout]"
    except Exception as e:
        yield f"[Error: {e}]"


async def async_generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> OllamaResponse:
    """Async generate completion for a single prompt.

    Args:
        prompt: The prompt text
        model: Model name
        system: Optional system prompt
        temperature: Sampling temperature
        max_tokens: Max response tokens
        timeout: Request timeout

    Returns:
        OllamaResponse with content and metadata
    """
    try:
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['system'] = system

        if max_tokens:
            payload['options']['num_predict'] = max_tokens

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return OllamaResponse(
                        content=data.get('response', ''),
                        model=data.get('model', model),
                        done=data.get('done', True),
                        total_duration=data.get('total_duration'),
                        load_duration=data.get('load_duration'),
                        prompt_eval_count=data.get('prompt_eval_count'),
                        eval_count=data.get('eval_count')
                    )
                else:
                    text = await resp.text()
                    return OllamaResponse(
                        content='',
                        model=model,
                        done=True,
                        error=f"HTTP {resp.status}: {text}"
                    )

    except aiohttp.ClientConnectorError:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error='Ollama not running'
        )
    except Exception as e:
        return OllamaResponse(
            content='',
            model=model,
            done=True,
            error=str(e)
        )


async def async_quick_ask(question: str, model: str = DEFAULT_MODEL) -> str:
    """Async quick single-turn question.

    Args:
        question: The question to ask
        model: Model to use

    Returns:
        Response text or error message
    """
    response = await async_chat(
        messages=[{'role': 'user', 'content': question}],
        model=model
    )
    if response.error:
        return f"[Error: {response.error}]"
    return response.content


if __name__ == "__main__":
    # Test Ollama connection
    print("=== OLLAMA API TEST ===")

    status = check_ollama()
    print(f"Connected: {status['connected']}")
    print(f"Models: {status['models']}")
    if status['model_names']:
        print(f"Available: {', '.join(status['model_names'][:5])}")
    if status['error']:
        print(f"Error: {status['error']}")

    if status['connected']:
        print("\n=== QUICK TEST ===")
        response = quick_ask("Say 'Hello from CORA!' in exactly 5 words.")
        print(f"Response: {response}")
