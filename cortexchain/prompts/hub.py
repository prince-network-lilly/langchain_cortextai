"""Prompt Hub — a registry of reusable prompt templates."""
import json
import os
from typing import Dict, List, Optional
from cortexchain.prompts.templates import PromptTemplate


_BUILT_IN_PROMPTS = {
    "summarize": {
        "template": "Summarize the following text in {style}:\n\n{text}\n\nSummary:",
        "description": "Summarize text in a given style (brief, detailed, bullet points)",
    },
    "translate": {
        "template": "Translate the following text to {language}:\n\n{text}\n\nTranslation:",
        "description": "Translate text to a target language",
    },
    "classify": {
        "template": "Classify the following text into one of these categories: {categories}\n\nText: {text}\n\nCategory:",
        "description": "Classify text into predefined categories",
    },
    "extract": {
        "template": "Extract the following information from the text: {fields}\n\nText: {text}\n\nExtracted (as JSON):",
        "description": "Extract structured fields from unstructured text",
    },
    "qa": {
        "template": "Answer the question based on the context below.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        "description": "Question-answering with context",
    },
    "code_review": {
        "template": "Review the following code for bugs, security issues, and improvements:\n\n```{language}\n{code}\n```\n\nReview:",
        "description": "Review code for issues and improvements",
    },
    "code_generate": {
        "template": "Write {language} code that does the following:\n\n{description}\n\nCode:",
        "description": "Generate code from a description",
    },
    "sentiment": {
        "template": "Analyze the sentiment of the following text. Respond with: positive, negative, or neutral.\n\nText: {text}\n\nSentiment:",
        "description": "Analyze text sentiment",
    },
    "rewrite": {
        "template": "Rewrite the following text to be {style}:\n\nOriginal: {text}\n\nRewritten:",
        "description": "Rewrite text in a different style (formal, casual, concise)",
    },
    "compare": {
        "template": "Compare and contrast the following:\n\nItem A: {item_a}\nItem B: {item_b}\n\nComparison:",
        "description": "Compare two items or concepts",
    },
}


class PromptHub:
    """Registry of reusable prompt templates — includes built-ins and supports custom prompts.

    Usage:
        hub = PromptHub()
        prompt = hub.get("summarize")
        result = prompt.format(text="...", style="brief")

        # Register custom prompts
        hub.register("my_prompt", "Do {action} with {input}", description="My custom prompt")

        # Save/load custom prompts to disk
        hub.save("./my_prompts")
        hub = PromptHub.load("./my_prompts")
    """

    def __init__(self, include_builtins: bool = True):
        self._prompts: Dict[str, Dict] = {}
        if include_builtins:
            self._prompts.update(_BUILT_IN_PROMPTS)

    def get(self, name: str) -> PromptTemplate:
        """Get a prompt template by name."""
        if name not in self._prompts:
            available = ", ".join(sorted(self._prompts.keys()))
            raise KeyError(f"Prompt {name!r} not found. Available: {available}")
        entry = self._prompts[name]
        return PromptTemplate.from_template(entry["template"])

    def register(self, name: str, template: str, description: str = "") -> None:
        """Register a custom prompt template."""
        self._prompts[name] = {
            "template": template,
            "description": description or f"Custom prompt: {name}",
        }

    def remove(self, name: str) -> None:
        """Remove a prompt from the registry."""
        self._prompts.pop(name, None)

    def list(self) -> List[Dict[str, str]]:
        """List all available prompts with their descriptions."""
        return [
            {"name": name, "description": entry["description"]}
            for name, entry in sorted(self._prompts.items())
        ]

    def search(self, keyword: str) -> List[Dict[str, str]]:
        """Search prompts by keyword in name or description."""
        keyword = keyword.lower()
        return [
            {"name": name, "description": entry["description"]}
            for name, entry in self._prompts.items()
            if keyword in name.lower() or keyword in entry.get("description", "").lower()
        ]

    def save(self, directory: str) -> None:
        """Save custom prompts to a directory."""
        os.makedirs(directory, exist_ok=True)
        custom = {k: v for k, v in self._prompts.items() if k not in _BUILT_IN_PROMPTS}
        path = os.path.join(directory, "prompts.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(custom, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, directory: str) -> "PromptHub":
        """Load a PromptHub with custom prompts from a directory."""
        hub = cls(include_builtins=True)
        path = os.path.join(directory, "prompts.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                custom = json.load(f)
            hub._prompts.update(custom)
        return hub

    def __contains__(self, name: str) -> bool:
        return name in self._prompts

    def __len__(self) -> int:
        return len(self._prompts)

    def __repr__(self) -> str:
        return f"PromptHub(prompts={len(self._prompts)})"
