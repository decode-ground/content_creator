"""Base Agent class - abstract base for all specialized agents."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

from app.core.llm import llm_client


# Type variable for agent output schemas
T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all specialized agents in the pipeline.

    Each agent is responsible for a specific task and uses the LLM client
    for reasoning and structured outputs. Agents should implement the
    execute method to define their core logic.

    Attributes:
        name: Human-readable name of the agent
        system_prompt: System-level instructions for the LLM
    """

    def __init__(self, name: str, system_prompt: str):
        """
        Initialize the agent with a name and system prompt.

        Args:
            name: Agent name for logging and identification
            system_prompt: System instructions that define the agent's role and behavior
        """
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> T:
        """
        Execute the agent's core logic.

        This method must be implemented by all concrete agents. It should:
        1. Validate input data
        2. Perform the agent's task (usually involving LLM calls)
        3. Return structured output as a Pydantic model

        Args:
            input_data: Dictionary containing all necessary inputs for the agent

        Returns:
            Pydantic model instance with structured output

        Raises:
            ValueError: If input data is invalid
            Exception: If agent execution fails
        """
        pass

    async def reason(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Perform chain-of-thought reasoning with the LLM.

        Use this method when you need the agent to reason through a problem
        and return a natural language response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response

        Returns:
            LLM's text response
        """
        return await llm_client.invoke(
            messages=messages,
            system=self.system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def reason_structured(
        self,
        messages: list[dict[str, str]],
        output_schema: type[T],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> T:
        """
        Perform reasoning and return structured output validated by a Pydantic schema.

        This is the preferred method for agents that need to return structured data.
        The LLM output will be automatically validated against the schema.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            output_schema: Pydantic model class defining the expected output structure
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Instance of output_schema with validated LLM output

        Raises:
            ValidationError: If LLM output doesn't match schema
        """
        return await llm_client.invoke_structured(
            messages=messages,
            system=self.system_prompt,
            output_schema=output_schema,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def reason_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> dict[str, Any]:
        """
        Perform reasoning and return JSON output.

        Use this when you need JSON output but don't have a predefined schema.
        For structured outputs with validation, prefer reason_structured().

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with parsed JSON response

        Raises:
            JSONDecodeError: If LLM output is not valid JSON
        """
        return await llm_client.invoke_json(
            messages=messages,
            system=self.system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"
