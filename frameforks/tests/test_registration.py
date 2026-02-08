import time
import uuid

from frameforks.internal.http.account import AccountApi
from frameforks.internal.http.mail import MailApi


def test_failed_registration(account: AccountApi, mail: MailApi):
    expected_mail = 'string@mail.ru'
    account.register_user(login='string', email=expected_mail, password='string')
    for _ in range(10):
        response = mail.find_message(query=expected_mail)
        if response.json()['total'] > 0:
            raise AssertionError('Email not found')
        time.sleep(1)


def test_success_registration(account: AccountApi, mail: MailApi):
    base = uuid.uuid4().hex

    account.register_user(login=base, email=f'{base}@mail.ru', password='123123')

    for _ in range(10):
        response = mail.find_message(query=base)
        if response.json()['total'] > 0:
            break
        time.sleep(1)
    else:
        raise AssertionError('Email not found')
