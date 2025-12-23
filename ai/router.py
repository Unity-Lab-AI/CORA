#!/usr/bin/env python3
"""
C.O.R.A Model Router
Intelligent model selection based on task type

Per ARCHITECTURE.md v2.0.0:
- Route queries to appropriate models
- Fast model for simple tasks
- Larger models for complex reasoning
- Keyword-based routing
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskType(Enum):
    """Types of tasks for routing."""
    SIMPLE = "simple"           # Quick answers, greetings
    CONVERSATION = "conversation"  # General chat
    REASONING = "reasoning"     # Complex analysis
    CODE = "code"               # Code generation/review
    CREATIVE = "creative"       # Creative writing
    FACTUAL = "factual"         # Fact lookup


# Model recommendations by capability
MODEL_TIERS = {
    'fast': [
        'llama3.2:1b',
        'phi3:mini',
        'gemma:2b',
        'tinyllama:1b'
    ],
    'balanced': [
        'llama3.2:3b',
        'phi3:medium',
        'gemma:7b',
        'mistral:7b'
    ],
    'powerful': [
        'llama3.1:8b',
        'codellama:13b',
        'deepseek-coder:6.7b',
        'mixtral:8x7b'
    ],
    'code': [
        'codellama:7b',
        'deepseek-coder:6.7b',
        'starcoder2:7b'
    ]
}


# Keywords that suggest task types
MODEL_KEYWORDS = {
    TaskType.SIMPLE: [
        'hi', 'hello', 'hey', 'thanks', 'bye', 'ok', 'yes', 'no',
        'good morning', 'good night', 'how are you'
    ],
    TaskType.CODE: [
        'code', 'function', 'class', 'python', 'javascript', 'debug',
        'error', 'bug', 'syntax', 'compile', 'script', 'program',
        'api', 'json', 'html', 'css', 'sql', 'git', 'npm'
    ],
    TaskType.REASONING: [
        'analyze', 'explain', 'why', 'how does', 'compare', 'evaluate',
        'think about', 'consider', 'reason', 'logic', 'argue', 'debate',
        'pros and cons', 'trade-offs', 'implications'
    ],
    TaskType.CREATIVE: [
        'write', 'story', 'poem', 'creative', 'imagine', 'describe',
        'fiction', 'novel', 'character', 'plot', 'scene'
    ],
    TaskType.FACTUAL: [
        'what is', 'who is', 'when did', 'where is', 'define',
        'fact', 'history', 'date', 'number', 'statistic'
    ]
}


@dataclass
class ModelRouter:
    """Routes queries to appropriate models."""

    default_model: str = "llama3.2:3b"
    fast_model: str = "llama3.2:1b"
    powerful_model: str = "llama3.1:8b"
    code_model: str = "codellama:7b"
    available_models: List[str] = field(default_factory=list)

    def detect_task_type(self, query: str) -> TaskType:
        """Detect the type of task from the query.

        Args:
            query: User's input text

        Returns:
            TaskType enum value
        """
        query_lower = query.lower().strip()

        # Check for simple greetings first (shortest queries)
        if len(query_lower) < 20:
            for keyword in MODEL_KEYWORDS[TaskType.SIMPLE]:
                if keyword in query_lower:
                    return TaskType.SIMPLE

        # Score each task type
        scores = {}
        for task_type, keywords in MODEL_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            scores[task_type] = score

        # Return highest scoring type
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        # Default to conversation
        return TaskType.CONVERSATION

    def select_model(
        self,
        query: str,
        prefer_fast: bool = False,
        prefer_powerful: bool = False
    ) -> Tuple[str, TaskType]:
        """Select the best model for a query.

        Args:
            query: User's input text
            prefer_fast: Prefer speed over quality
            prefer_powerful: Prefer quality over speed

        Returns:
            Tuple of (model_name, task_type)
        """
        task_type = self.detect_task_type(query)

        # Override preferences
        if prefer_fast:
            return (self.fast_model, task_type)
        if prefer_powerful:
            return (self.powerful_model, task_type)

        # Route based on task type
        if task_type == TaskType.SIMPLE:
            return (self.fast_model, task_type)
        elif task_type == TaskType.CODE:
            return (self.code_model, task_type)
        elif task_type == TaskType.REASONING:
            return (self.powerful_model, task_type)
        elif task_type == TaskType.CREATIVE:
            return (self.powerful_model, task_type)
        else:
            return (self.default_model, task_type)

    def get_model_for_type(self, task_type: TaskType) -> str:
        """Get recommended model for a task type.

        Args:
            task_type: The type of task

        Returns:
            Model name string
        """
        mapping = {
            TaskType.SIMPLE: self.fast_model,
            TaskType.CONVERSATION: self.default_model,
            TaskType.REASONING: self.powerful_model,
            TaskType.CODE: self.code_model,
            TaskType.CREATIVE: self.powerful_model,
            TaskType.FACTUAL: self.default_model
        }
        return mapping.get(task_type, self.default_model)

    def set_available_models(self, models: List[str]):
        """Set the list of available models.

        Args:
            models: List of model names from Ollama
        """
        self.available_models = models

        # Update defaults based on what's available
        for model in models:
            model_lower = model.lower()

            # Update fast model
            if any(fast in model_lower for fast in ['1b', ':1b', 'tinyllama', 'phi3:mini']):
                self.fast_model = model

            # Update code model
            if any(code in model_lower for code in ['codellama', 'deepseek-coder', 'starcoder']):
                self.code_model = model

            # Update powerful model
            if any(big in model_lower for big in ['8b', '13b', 'mixtral']):
                self.powerful_model = model

    def validate_model(self, model: str) -> bool:
        """Check if a model is available.

        Args:
            model: Model name to check

        Returns:
            True if available
        """
        if not self.available_models:
            return True  # Assume available if not checked
        return model in self.available_models


def select_model(
    query: str,
    available_models: Optional[List[str]] = None,
    prefer_fast: bool = False,
    prefer_powerful: bool = False
) -> Tuple[str, str]:
    """Convenience function to select a model.

    Args:
        query: User's input
        available_models: Optional list of available models
        prefer_fast: Prefer speed
        prefer_powerful: Prefer quality

    Returns:
        Tuple of (model_name, task_type_name)
    """
    router = ModelRouter()

    if available_models:
        router.set_available_models(available_models)

    model, task_type = router.select_model(
        query,
        prefer_fast=prefer_fast,
        prefer_powerful=prefer_powerful
    )

    return (model, task_type.value)


def get_model_recommendation(task_description: str) -> Dict[str, Any]:
    """Get model recommendation with explanation.

    Args:
        task_description: Description of what needs to be done

    Returns:
        Dict with model, task_type, reason
    """
    router = ModelRouter()
    task_type = router.detect_task_type(task_description)
    model = router.get_model_for_type(task_type)

    reasons = {
        TaskType.SIMPLE: "Simple query - using fast model for quick response",
        TaskType.CONVERSATION: "General conversation - using balanced model",
        TaskType.REASONING: "Complex reasoning - using powerful model",
        TaskType.CODE: "Code-related task - using code-specialized model",
        TaskType.CREATIVE: "Creative task - using powerful model for quality",
        TaskType.FACTUAL: "Factual lookup - using balanced model"
    }

    return {
        'model': model,
        'task_type': task_type.value,
        'reason': reasons.get(task_type, "Using default model")
    }


def estimate_complexity(query: str) -> Dict[str, Any]:
    """Estimate query complexity.

    Args:
        query: The query text

    Returns:
        Dict with complexity score and factors
    """
    factors = {
        'length': len(query),
        'word_count': len(query.split()),
        'has_code': bool(re.search(r'```|def |class |function |import ', query)),
        'has_question': '?' in query,
        'multi_part': query.count('?') > 1 or 'and' in query.lower(),
        'technical_terms': 0
    }

    # Count technical terms
    technical = ['algorithm', 'architecture', 'implementation', 'optimize',
                 'performance', 'scalability', 'security', 'database']
    for term in technical:
        if term in query.lower():
            factors['technical_terms'] += 1

    # Calculate complexity score (0-10)
    score = 0
    if factors['word_count'] > 50:
        score += 2
    if factors['has_code']:
        score += 3
    if factors['multi_part']:
        score += 2
    if factors['technical_terms'] > 0:
        score += min(factors['technical_terms'], 3)

    factors['score'] = min(score, 10)
    factors['level'] = 'simple' if score < 3 else 'moderate' if score < 6 else 'complex'

    return factors


if __name__ == "__main__":
    # Test router
    print("=== MODEL ROUTER TEST ===")

    test_queries = [
        "Hi there!",
        "What's the weather like?",
        "Write a Python function to sort a list",
        "Explain the implications of quantum computing on cryptography",
        "Write me a short poem about coding",
        "What is the capital of France?"
    ]

    router = ModelRouter()

    for query in test_queries:
        model, task_type = router.select_model(query)
        print(f"\nQuery: {query[:50]}...")
        print(f"  Task: {task_type.value}")
        print(f"  Model: {model}")

    print("\n=== COMPLEXITY TEST ===")
    complex_query = "Write a Python class that implements a binary search tree with insert, delete, and search methods, then analyze its time complexity."
    complexity = estimate_complexity(complex_query)
    print(f"Query: {complex_query[:60]}...")
    print(f"Complexity: {complexity['level']} (score: {complexity['score']})")
