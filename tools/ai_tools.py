"""
C.O.R.A AI Tools Module

AI-powered tool integrations for CORA.
Per ARCHITECTURE.md: Image gen, code gen, summarization, web search.
"""

import json
import subprocess
import urllib.request
import urllib.error


# Ollama API settings
OLLAMA_URL = "http://localhost:11434"


def check_ollama():
    """Check if Ollama is running.

    Returns:
        bool: True if Ollama is accessible
    """
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def list_models():
    """List available Ollama models.

    Returns:
        list: Model names or empty list if error
    """
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return [m['name'] for m in data.get('models', [])]
    except Exception as e:
        print(f"[!] Failed to list models: {e}")
        return []


def pull_model(model_name, progress_callback=None):
    """Pull/download an Ollama model.

    Args:
        model_name: Name of model to pull (e.g., 'llama3.2')
        progress_callback: Optional callback for progress updates

    Returns:
        bool: True if pulled successfully
    """
    try:
        result = subprocess.run(
            ['ollama', 'pull', model_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("[!] Model pull timed out")
        return False
    except Exception as e:
        print(f"[!] Failed to pull model: {e}")
        return False


def chat(prompt, model='llama3.2', system_prompt=None, history=None):
    """Chat with Ollama model.

    Args:
        prompt: User message
        model: Model name to use
        system_prompt: Optional system prompt
        history: Optional chat history

    Returns:
        str: AI response or error message
    """
    try:
        messages = []

        # Add system prompt
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})

        # Add history
        if history:
            messages.extend(history)

        # Add current prompt
        messages.append({'role': 'user', 'content': prompt})

        payload = {
            'model': model,
            'messages': messages,
            'stream': False
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            return result.get('message', {}).get('content', '')

    except urllib.error.URLError:
        return "[!] Ollama not running. Start with: ollama serve"
    except Exception as e:
        return f"[!] Chat error: {e}"


def generate_code(description, language='python', model='llama3.2'):
    """Generate code from description.

    Args:
        description: What the code should do
        language: Programming language
        model: Model to use

    Returns:
        str: Generated code or error message
    """
    system_prompt = f"""You are a {language} code generator.
Generate clean, well-commented code based on the user's description.
Only output code, no explanations unless asked.
Use best practices and modern syntax."""

    prompt = f"Generate {language} code that: {description}"
    return chat(prompt, model=model, system_prompt=system_prompt)


def explain_code(code, language='python', model='llama3.2'):
    """Explain what code does.

    Args:
        code: Code to explain
        language: Programming language
        model: Model to use

    Returns:
        str: Explanation or error message
    """
    system_prompt = """You are a code explainer.
Explain code clearly and concisely.
Break down complex parts.
Mention any potential issues or improvements."""

    prompt = f"Explain this {language} code:\n```{language}\n{code}\n```"
    return chat(prompt, model=model, system_prompt=system_prompt)


def summarize_text(text, max_sentences=3, model='llama3.2'):
    """Summarize text.

    Args:
        text: Text to summarize
        max_sentences: Maximum sentences in summary
        model: Model to use

    Returns:
        str: Summary or error message
    """
    system_prompt = f"""You are a summarizer.
Summarize the given text in {max_sentences} sentences or fewer.
Focus on key points.
Be concise but complete."""

    prompt = f"Summarize this text:\n\n{text}"
    return chat(prompt, model=model, system_prompt=system_prompt)


def analyze_sentiment(text, model='llama3.2'):
    """Analyze sentiment of text.

    Args:
        text: Text to analyze
        model: Model to use

    Returns:
        dict: Sentiment analysis result
    """
    system_prompt = """You are a sentiment analyzer.
Analyze the sentiment and return JSON only.
Format: {"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0, "emotions": ["list", "of", "emotions"]}"""

    prompt = f"Analyze the sentiment of this text:\n\n{text}"
    response = chat(prompt, model=model, system_prompt=system_prompt)

    try:
        # Try to parse as JSON
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            'sentiment': 'unknown',
            'confidence': 0.0,
            'raw_response': response
        }


def translate_text(text, target_language, model='llama3.2'):
    """Translate text to another language.

    Args:
        text: Text to translate
        target_language: Target language name (e.g., 'Spanish')
        model: Model to use

    Returns:
        str: Translated text or error message
    """
    system_prompt = f"""You are a translator.
Translate the given text to {target_language}.
Only output the translation, no explanations."""

    prompt = f"Translate to {target_language}:\n\n{text}"
    return chat(prompt, model=model, system_prompt=system_prompt)


def suggest_task_priority(task_description, context=None, model='llama3.2'):
    """Suggest priority for a task.

    Args:
        task_description: Task to evaluate
        context: Optional context (other tasks, deadlines)
        model: Model to use

    Returns:
        dict: Priority suggestion with reasoning
    """
    system_prompt = """You are a task prioritization assistant.
Analyze the task and suggest a priority from 1-10 (1 is highest priority).
Return JSON only: {"priority": 1-10, "reasoning": "brief explanation"}"""

    prompt = f"Suggest priority for this task: {task_description}"
    if context:
        prompt += f"\n\nContext: {context}"

    response = chat(prompt, model=model, system_prompt=system_prompt)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            'priority': 5,
            'reasoning': 'Could not analyze',
            'raw_response': response
        }


def generate_response(context, personality, user_input, model='llama3.2'):
    """Generate a CORA-style response.

    Args:
        context: Current system context (tasks, state)
        personality: Personality settings dict
        user_input: User's message
        model: Model to use

    Returns:
        str: Generated response
    """
    # Build system prompt from personality
    system_prompt = f"""You are {personality.get('name', 'CORA')}.
Identity: {personality.get('identity', 'personal assistant')}
Tone: {personality.get('personality', {}).get('tone', 'helpful')}
Style: {personality.get('personality', {}).get('style', 'professional')}

NEVER say: {', '.join(personality.get('never_say', []))}

Current context: {context}

Respond naturally in character. Keep responses concise (under 30 words unless explaining something complex)."""

    return chat(user_input, model=model, system_prompt=system_prompt)


def extract_keywords(text, max_keywords=5, model='llama3.2'):
    """Extract keywords from text.

    Args:
        text: Text to analyze
        max_keywords: Maximum keywords to extract
        model: Model to use

    Returns:
        list: Keywords
    """
    system_prompt = f"""You are a keyword extractor.
Extract up to {max_keywords} important keywords from the text.
Return as JSON array only: ["keyword1", "keyword2", ...]"""

    prompt = f"Extract keywords from:\n\n{text}"
    response = chat(prompt, model=model, system_prompt=system_prompt)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract from raw response
        words = [w.strip() for w in response.replace('[', '').replace(']', '').replace('"', '').split(',')]
        return words[:max_keywords]


def ask_question(question, context=None, model='llama3.2'):
    """Ask a general question.

    Args:
        question: Question to ask
        context: Optional context
        model: Model to use

    Returns:
        str: Answer
    """
    system_prompt = """You are a helpful assistant.
Answer questions accurately and concisely.
If you don't know something, say so."""

    prompt = question
    if context:
        prompt = f"Context: {context}\n\nQuestion: {question}"

    return chat(prompt, model=model, system_prompt=system_prompt)
