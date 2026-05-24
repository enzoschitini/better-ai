from typing import List, Any

from agno.tools import Toolkit
from src.agents.utils.tool_response import ToolResponse

class BaseToolkit(Toolkit):
    """
    BaseToolkit is a generic toolkit template for building agent tools.

    Use this as a starting point for creating new toolkits by:
    - Renaming the class to reflect the toolkit's domain
    - Adding domain-specific tools as methods
    - Registering them in the `tools` list inside `__init__`

    Args:
        enable_get_current_datetime (bool): Enable the current datetime tool. Default is True.
        enable_get_temperature (bool): Enable the temperature tool. Default is True.
        all (bool): Enable all tools. Overrides individual flags when True. Default is False.
        TOOL_RESPONSER (ToolResponse): Optional metadata collector. Default is None.
    """
    def __init__(
        self,
        enable_get_current_datetime: bool = True,
        enable_get_temperature: bool = True,
        all: bool = False,
        TOOL_RESPONSER: ToolResponse = None,
        **kwargs,
    ):
        self.TOOL_RESPONSER = TOOL_RESPONSER
        tools: List[Any] = []

        if all or enable_get_current_datetime:
            tools.append(self.get_current_datetime)

        if all or enable_get_temperature:
            tools.append(self.get_temperature)

        super().__init__(name="base_toolkit", tools=tools, **kwargs)

    def _update_response(self, tool_name: str, payload: dict):
        """
        Internal helper to collect metadata about tool execution.
        """
        if self.TOOL_RESPONSER:
            self.TOOL_RESPONSER.add_metadata(
                tool_name=tool_name,
                payload=payload
            )

    def get_current_datetime(self, query: str) -> str:
        """
        Returns the current date and time based on the user's query.

        Args:
            query (str): The user's input query. Must be a non-empty string.

        Returns:
            str: The current date and time as a formatted string.
        """
        try:
            from datetime import datetime
            import random

            if not query or not query.strip():
                return "A valid query is required."

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self._update_response(
                "get_current_datetime",
                {"query": query, "datetime": now}
            )

        except Exception as e:
            return f"Failed to get current datetime: {str(e)}"

        return now

    def get_temperature(self, city: str) -> str:
        """
        Returns the current temperature for a given city.

        This is a placeholder tool that simulates a weather API response.
        Replace this method with a real weather API integration when needed.

        Args:
            city (str):
                The name of the city to retrieve the temperature for.
                Must be a non-empty string.

        Returns:
            str: A message containing the city name and its current temperature in Celsius.
        """
        try:
            import random
            
            if not city or not city.strip():
                return "A valid city name is required."

            fake_temperature = round(random.uniform(10.0, 40.0), 1)

            self._update_response(
                "get_temperature",
                {"city": city, "temperature_celsius": fake_temperature}
            )

        except Exception as e:
            return f"Failed to get temperature: {str(e)}"

        return f"The current temperature in {city} is {fake_temperature}°C."


if __name__ == "__main__":
    toolkit = BaseToolkit()

    datetime_result = toolkit.get_current_datetime("What is the current date and time?")
    print(f"\n{datetime_result}")

    temperature_result = toolkit.get_temperature("Salvador")
    print(f"{temperature_result}\n")


# python -m src.agents._base_agent.tools.toolkit