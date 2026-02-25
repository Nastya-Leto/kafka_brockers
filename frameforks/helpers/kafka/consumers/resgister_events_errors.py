from frameforks.internal.kafka.subscriber import Subscriber
import queue


class RegisterEventsErrorsSubscriber(Subscriber):
    topic: str = 'register-events-errors'

    def find_message(self, login, error_type, timeout: int = 90):
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