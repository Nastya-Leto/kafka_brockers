import json
import time
import uuid

import pytest
import pika

from frameforks.helpers.kafka.consumers.register_events import RegisterEventsSubscriber
from frameforks.helpers.kafka.consumers.resgister_events_errors import RegisterEventsErrorsSubscriber
from frameforks.internal.http.account import AccountApi
from frameforks.internal.kafka.producer import KafkaProducer
from frameforks.internal.http.mail import MailApi
from frameforks.internal.rmq.publischer import RmqPublisher


@pytest.fixture
def register_message() -> dict[str, str]:
    base = uuid.uuid4().hex
    return {'login': base, 'email': f'{base}@mail.ru', 'password': '123123n'}


@pytest.fixture
def invalid_register_message() -> dict[str, str]:
    base = uuid.uuid4().hex
    return {'login': base, 'email': '', 'password': 'string1'}


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


def test_success_registration_with_kafka_producer(mail: MailApi, kafka_producer: KafkaProducer):
    base = uuid.uuid4().hex
    message = {'login': base, 'email': f'{base}@mail.ru', 'password': '123123'}
    kafka_producer.send('register-events', message)

    for _ in range(10):
        response = mail.find_message(query=base)
        if response.json()['total'] > 0:
            break
        time.sleep(1)

    else:
        raise AssertionError('Email not found')


def test_register_events_error_consumer(mail: MailApi, kafka_producer: KafkaProducer, account: AccountApi):
    base = uuid.uuid4().hex

    message = {
        "input_data": {
            "login": base,
            "email": f'{base}@mail.ru',
            "password": '123123123n'
        },
        "error_message": {
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Validation failed",
            "status": 400,
            "traceId": "00-2bd2ede7c3e4dcf40c4b7a62ac23f448-839ff284720ea656-01",
            "errors": {
                "Email": [
                    "Invalid"
                ]
            }
        },
        "error_type": "unknown"
    }
    kafka_producer.send('register-events-errors', message)

    for _ in range(10):
        # Поиск сообщения на почтовом сервере
        response = mail.find_message(query=base)
        if response.json()['total'] > 0:
            # Получение токена из письма
            token = mail.get_activation_token_by_login(response, login=base)
            # Активация пользователя
            response = account.activate_user(token)
            assert response.json().get('resource').get('login') == base
            break
        time.sleep(1)
    else:
        raise AssertionError('Email not found')


def test_success_registration_with_kafka_producer_consumer(register_events_subscriber: RegisterEventsSubscriber,
                                                           kafka_producer: KafkaProducer) -> None:
    base = uuid.uuid4().hex
    message = {'login': base, 'email': f'{base}@mail.ru', 'password': '1231231614'}
    kafka_producer.send('register-events', message)
    for i in range(10):
        message = register_events_subscriber.get_message()
        if isinstance(message.value, dict) and 'login' in message.value:
            if base == message.value['login']:
                break
    else:
        raise AssertionError('login not found')


def test_success_registration_end_2_end(
        register_events_subscriber: RegisterEventsSubscriber,
        register_message: dict[str, str],
        account: AccountApi,
        mail: MailApi):
    login = register_message['login']
    print(f'login:{login}')
    account.register_user(**register_message)
    register_events_subscriber.find_message(login)

    for _ in range(10):
        response = mail.find_message(query=login)
        if response.json()['total'] > 0:
            break
        time.sleep(1)
    else:
        raise AssertionError('Email not found')


def test_failed_registration_end_2_end(register_events_subscriber: RegisterEventsSubscriber,
                                       register_events_errors_subscriber: RegisterEventsErrorsSubscriber,
                                       invalid_register_message: dict[str, str],
                                       account: AccountApi):
    login = invalid_register_message['login']
    print(f'login:{login}')
    account.register_user(**invalid_register_message)
    register_events_subscriber.find_message(login)
    register_events_errors_subscriber.find_message(login, error_type='validation')


def test_invalid_message_end_2_end(kafka_producer: KafkaProducer,
                                   register_events_subscriber: RegisterEventsSubscriber,
                                   register_events_errors_subscriber: RegisterEventsErrorsSubscriber,
                                   invalid_register_message: dict[str, str],
                                   account: AccountApi):
    login = uuid.uuid4().hex

    message = {
        "input_data": {
            "login": login,
            "email": "string@mail.ru",
            "password": 'string'
        },
        "error_message": {
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Validation failed",
            "status": 400,
            "traceId": "00-2bd2ede7c3e4dcf40c4b7a62ac23f448-839ff284720ea656-01",
            "errors": {
                "Email": [
                    "Taken"
                ]
            }
        },
        "error_type": "unknown"
    }
    kafka_producer.send('register-events-errors', message)
    register_events_errors_subscriber.find_message(login, error_type='unknown')
    register_events_errors_subscriber.find_message(login, error_type='validation')


def test_rmq(rmq_producer: RmqPublisher) -> None:
    address = f'{uuid.uuid4().hex}@mail.ru'
    message = {
        'address': address,
        'subject': 'Publish message',
        'body': 'Test message'
    }
    rmq_producer.publish(exchange='dm.mail.sending', message=message)


def test_rmq_with_search_mail(rmq_producer: RmqPublisher,
                              mail: MailApi) -> None:
    address = f'{uuid.uuid4().hex}@mail.ru'
    message = {
        'address': address,
        'subject': 'Publish message',
        'body': 'Publish message'
    }
    rmq_producer.publish(exchange='dm.mail.sending', message=message)

    for _ in range(10):
        response = mail.find_message(query=address)
        if response.json()['total'] > 0:
            break
        time.sleep(1)
    else:
        raise AssertionError('Email not found')
