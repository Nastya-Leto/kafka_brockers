import pytest
from frameforks.internal.http.account import AccountApi
from frameforks.internal.http.mail import MailApi
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
