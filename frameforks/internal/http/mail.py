from json import loads

import httpx


class MailApi:

    def __init__(self, base_url: str = 'http://185.185.143.231:8085') -> None:
        self._base_url = base_url
        self._client = httpx.Client(base_url=self._base_url)

    def find_message(self, query: str):
        params = {
            "query": query,
            "limit": 1,
            "kind": 'containing',
            "start": 0
        }
        response = self._client.get('/mail/mail/search', params=params)
        print(f'find_message: {response.json()}')
        return response

    @staticmethod
    def get_activation_token_by_login(response, login):
        token = None
        resp_js = response.json()
        for item in resp_js['items']:
            user_data = loads(item['Content']['Body'])
            user_login = user_data['Login']
            if user_login == login:
                token = user_data['ConfirmationLinkUrl'].split('/')[-1]
                assert token is not None, 'Токен отсутствует'
        return token
