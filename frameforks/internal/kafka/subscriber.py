from abc import ABC, abstractmethod
import queue

from kafka.consumer.fetcher import ConsumerRecord


class Subscriber(ABC):
    def __init__(self):
        self._messages: queue.Queue = queue.Queue()

    @property
    @abstractmethod
    def topic(self) -> str:
        ...

    def handle_message(self, record: ConsumerRecord) -> None:
        """
        Говорит что делать при получении события
        Добавление сообщения в очередь
        """
        self._messages.put(record)

    def get_message(self, timeout: int = 90):
        try:
            message = self._messages.get(timeout=timeout)
            print(f'message:{message}')
            return message
        except queue.Empty:
            raise AssertionError(f'No messages from topic: {self.topic}, within timeout {timeout}')

    def find_message(self, login, timeout: int = 90):
        for _ in range(10):
            try:
                message = self._messages.get(timeout=timeout)
                print(f'message:{message}')
                if isinstance(message.value, dict) and message.value.get('login') == login:
                    return message.value
                else:
                    continue
            except queue.Empty:
                raise AssertionError(f'No messages from topic: {self.topic}, within timeout {timeout}')

    def find_message_events_errors(self, login, error_type, timeout: int = 90):
        for _ in range(10):
            try:
                message = self._messages.get(timeout=timeout)
                print(f'message:{message}')
                if isinstance(message.value, dict) and message.value.get('input_data').get('login') == login:
                    if message.value.get('error_type') == error_type:
                        return True
                else:
                    continue
            except queue.Empty:
                raise AssertionError(f'No messages from topic: {self.topic}, within timeout {timeout}')
