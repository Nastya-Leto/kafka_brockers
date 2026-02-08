import pytest
from frameforks.internal.http.account import AccountApi
from frameforks.internal.http.mail import MailApi


@pytest.fixture(scope='session')
def account() -> AccountApi:
    return AccountApi()


@pytest.fixture(scope='session')
def mail() -> MailApi:
    return MailApi()
