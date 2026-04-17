import inspect
import json
from typing import Any, Awaitable, Callable, Dict, List


Event = Dict[str, Any]
Subscriber = Callable[[Event], Any]


class EventBus:
    """Simple async event bus with console output by default."""

    def __init__(self):
        self.subscribers: List[Subscriber] = [self._console_subscriber]

    def subscribe(self, callback: Subscriber) -> None:
        self.subscribers.append(callback)

    async def publish(self, event: Event) -> None:
        for subscriber in self.subscribers:
            result = subscriber(event)
            if inspect.isawaitable(result):
                await result

    @staticmethod
    def _console_subscriber(event: Event) -> None:
        print(json.dumps(event))

