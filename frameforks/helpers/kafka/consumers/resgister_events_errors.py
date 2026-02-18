from frameforks.internal.kafka.subscriber import Subscriber


class RegisterEventsErrorsSubscriber(Subscriber):
    topic: str = 'register-events-errors'