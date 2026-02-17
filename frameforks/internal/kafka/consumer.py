import json
import threading
import time

from black.trans import defaultdict
from kafka import KafkaConsumer

from frameforks.internal.kafka.singleton import Singleton
from frameforks.internal.kafka.subscriber import Subscriber


class Consumer(Singleton):
    _started: bool = False

    def __init__(self,
                 subscribers: list[Subscriber],
                 bootstrap_servers=['185.185.143.231:9092']
                 ):
        self._bootstrap_servers = bootstrap_servers
        self._subscribers = subscribers
        self._consumer: KafkaConsumer | None = None
        self._running = threading.Event()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._watchers: dict[str, list[Subscriber]] = defaultdict(list)

    def register(self):
        if self._subscribers is None:
            raise RuntimeError('Subscriber is not initialized')
        if self._started is True:
            raise RuntimeError('Consumer is already started')
        for subscriber in self._subscribers:
            print(f'Registering subscriber {subscriber.topic}')
            self._watchers[subscriber.topic].append(subscriber)

    def start(self):
        self._consumer = KafkaConsumer(*self._watchers.keys(),
                                       bootstrap_servers=self._bootstrap_servers,
                                       auto_offset_reset='latest',  # earliest самые ранние сообщения
                                       value_deserializer=lambda x: json.loads(x.decode('utf-8')))
        self._running.set()
        self._ready.clear()
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._thread.start()

        if not self._ready.wait(timeout=10):
            raise RuntimeError('Consumer is not ready')

        self._started = True

    def _consume(self):
        self._ready.set()
        print('Consumer started')
        try:
            while self._running.is_set():
                messages = self._consumer.poll(timeout_ms=1000, max_records=10)
                for topic_partition, records in messages.items():
                    topic = topic_partition.topic
                    for record in records:
                        for watcher in self._watchers[topic]:
                            watcher.handle_message(record)
                            print(f'{topic_partition}:{records}')
                    time.sleep(0.01)
                    if not messages:
                        time.sleep(0.01)
        except Exception as e:
            print(f'Error {e}')

    def stop(self):
        self._running.clear()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                print('thread is still alive')
        if self._consumer:
            try:
                self._consumer.close(timeout_ms=2000)
                print('stop consuming')
            except Exception as e:
                print(f'Error while closing consumer: {e}')

        del self._consumer
        self._watchers.clear()
        self._subscribers.clear()
        self._started = False

        print('consumer stopped')

    def __enter__(self):
        self.register()
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


if __name__ == '__main__':
    with Consumer() as consumer:
        message = consumer.get_message()
        print(message)
