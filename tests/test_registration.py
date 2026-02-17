import time
import uuid

from frameforks.helpers.kafka.consumers.register_events import RegisterEventsSubscriber
from frameforks.internal.http.account import AccountApi
from frameforks.internal.kafka.producer import KafkaProducer
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
