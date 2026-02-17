import pytest

from frameforks.helpers.kafka.consumers.register_events import RegisterEventsSubscriber
from frameforks.internal.http.account import AccountApi
from frameforks.internal.http.mail import MailApi
from frameforks.internal.kafka.consumer import Consumer
from frameforks.internal.kafka.producer import Producer


@pytest.fixture(scope='session')
def account() -> AccountApi:
    return AccountApi()


@pytest.fixture(scope='session')
def mail() -> MailApi:
    return MailApi()


@pytest.fixture(scope='session')
def kafka_producer() -> Producer:
    with Producer() as producer:
        yield producer


@pytest.fixture(scope='session')
def register_events_subscriber() -> RegisterEventsSubscriber:
    return RegisterEventsSubscriber()


@pytest.fixture(scope='session', autouse=True)
def kafka_consumer(register_events_subscriber:RegisterEventsSubscriber) -> Consumer:
    with Consumer(subscribers=[register_events_subscriber]) as consumer:
        yield consumer
