"""
hello-world - Example RappterHub Agent

A simple demonstration agent showing the standard structure and patterns.
"""

import json
from datetime import datetime

# Import BasicAgent if available (when running in openrappter)
try:
    from openrappter.agents.basic_agent import BasicAgent
except ImportError:
    # Standalone mode - define minimal BasicAgent
    class BasicAgent:
        def __init__(self, name: str, metadata: dict):
            self.name = name
            self.metadata = metadata
            self.context = {}

        def execute(self, **kwargs) -> str:
            return self.perform(**kwargs)

        def perform(self, **kwargs) -> str:
            raise NotImplementedError


class HelloWorldAgent(BasicAgent):
    """
    Hello World Agent - A simple example demonstrating RappterHub agent patterns.
    """

    def __init__(self):
        metadata = {
            "name": "hello-world",
            "description": "A simple example agent that demonstrates the RappterHub agent format",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A greeting or question"
                    }
                },
                "required": []
            }
        }
        super().__init__("hello-world", metadata)

    def perform(self, **kwargs) -> str:
        """
        Process a greeting or question.

        Args:
            query: The user's message

        Returns:
            JSON response with greeting or information
        """
        query = kwargs.get("query", "").lower().strip()

        # Handle different types of queries
        if any(greeting in query for greeting in ["hello", "hi", "hey", "greetings"]):
            return json.dumps({
                "status": "success",
                "message": "Hello! I'm a RappterHub agent. Nice to meet you!",
                "timestamp": datetime.now().isoformat()
            })

        if "what can you do" in query or "help" in query or "about" in query:
            return json.dumps({
                "status": "success",
                "message": "I'm a simple example agent from RappterHub. I can respond to greetings and tell you about myself. I'm meant to serve as a template for creating your own agents.",
                "capabilities": [
                    "Respond to greetings",
                    "Provide information about myself",
                    "Demonstrate standard agent patterns"
                ]
            })

        if "time" in query:
            return json.dumps({
                "status": "success",
                "message": f"The current time is {datetime.now().strftime('%H:%M:%S')}",
                "timestamp": datetime.now().isoformat()
            })

        # Default response
        return json.dumps({
            "status": "info",
            "message": f"I received: '{kwargs.get('query', '')}'. Try saying 'hello' or asking 'what can you do?'",
            "hint": "I'm a simple example agent - I respond to greetings and basic questions."
        })


# Allow direct execution for testing
if __name__ == "__main__":
    agent = HelloWorldAgent()

    print("Testing hello-world agent:")
    print("-" * 40)

    tests = [
        "hello",
        "what can you do?",
        "what time is it?",
        "random query"
    ]

    for test in tests:
        print(f"\nQuery: {test}")
        result = agent.execute(query=test)
        print(f"Response: {result}")
