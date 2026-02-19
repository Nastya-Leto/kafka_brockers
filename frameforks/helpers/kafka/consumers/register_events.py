from frameforks.internal.kafka.subscriber import Subscriber
import queue


class RegisterEventsSubscriber(Subscriber):
    topic: str = 'register-events'

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
