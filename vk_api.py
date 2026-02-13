import json
from json.decoder import WHITESPACE
from typing import Generic, TypeVar, Type, Literal
from pprint import pprint

import pydantic
import requests
from pydantic import BaseModel

from auth import AuthData
from models import ErrorModel, ErrorResponseModel, AddLikeModel, PostModel, PostsResponseModel

T = TypeVar("T", bound=BaseModel)


class VkApiError(Exception):
    """Ошибка в работе VkApi"""


class VkApi(Generic[T]):
    model: Type[T]
    based_url = "https://api.vk.com/method"

    _post_methods = [
        "likes.add",
        "captchaNotRobot.endSession",
        "captchaNotRobot.check",
        "captchaNotRobot.componentDone",
        "captchaNotRobot.settings",
    ]
    _get_methods = ["wall.get"]

    def __init__(self, request_session: requests.Session, auth_session: AuthData):
        self._session = request_session
        self._data = {}
        self._default_data = {"access_token": auth_session.access_token}

        self._captcha_params = {"v": "5.131"}
        self._liker_params = {"v": "5.269", "client_id": auth_session.client_id}
        self._access_token = auth_session.access_token
        self._expires = auth_session.expires
        self._cookies = auth_session.cookies

    def _handle_error(self, error: ErrorModel) -> None:
        pass

    # Зато если в качетсве аргумента передать модель без типизации, то вернеться либо она либо ошибка, так что пофиг
    # Можно сделать базовую АПИ как с репами и просто наплодить классов под каждый вид запрсов, где будут свои модели ответы
    # Сделать отдельный класс fetcher который будет плодиться так же как и с репами, но там будут токо эти запросы и ответы моедлями
    # и получается прямо тут в VkApi будем использовать эти фетчеры(они гдето же будут созданы). а тут по хорошему принимать нужные параметры и все

    def get_fetch_res(self, res: requests.Response) -> T:
        try:
            assert res.status_code == 200
            res_json = res.json()
            if res_json.get("error") is not None:
                return ErrorModel(**res_json)

            return self.model(**res_json)
        except json.JSONDecodeError:
            raise VkApiError(f"Could not get JSON from response: {res.text}")
        except pydantic.ValidationError as e:
            raise VkApiError(
                f"Could not create ErrorModel\nResponse: {pprint(res.text)}\nValidateError: {pprint(e)}"
            )
        except Exception as e:
            raise VkApiError(
                f"Could not get response, status_code: {res.status_code}\nerror: {e}"
            )


    def get_wall(self, owner_id: int, start_from: int):
        res = self._session.get(
            self.based_url + '/wall.get',
            params=self._liker_params,
            data={
                "extended": "1",
                "filters": "post",
                "filter": "owner",
                "domain": "-" + str(owner_id),
                "start_from": str(start_from),
                "count": "100",
                **self._default_data
            }
        )
        try:
            assert res.status_code == 200
            res_json = res.json()
            if res_json.get("error") is not None:
                return ErrorModel(**res_json)

            return PostsResponseModel(**res_json)
        except json.JSONDecodeError:
            raise VkApiError(f"Could not get JSON from response: {res.text}")
        except pydantic.ValidationError as e:
            raise VkApiError(
                f"Could not create ErrorModel\nResponse: {pprint(res.text)}\nValidateError: {pprint(e)}"
            )
        except Exception as e:
            raise VkApiError(
                f"Could not get response, status_code: {res.status_code}\nerror: {e}"
            )

    def add_like(self, post_model: PostModel) -> ErrorModel | None:
        res = self._session.post(
            self.based_url + "/likes.add",
            params=self._liker_params,
            data={
                **self._default_data,
                **post_model.model_dump(),
                "ref": "group",
                "reaction_id": 0,
            },
        )
        try:
            assert res.status_code == 200
            res_json = res.json()
            if res_json.get("error") is not None:
                return ErrorModel(**res_json)
        except json.JSONDecodeError:
            raise VkApiError(f"Could not get JSON from response: {res.text}")
        except pydantic.ValidationError as e:
            raise VkApiError(
                f"Could not create ErrorModel\nResponse: {pprint(res.text)}\nValidateError: {pprint(e)}"
            )
        except Exception as e:
            raise VkApiError(
                f"Could not get response, status_code: {res.status_code}\nerror: {e}"
            )

    def _fetch(
        self, method: str, data: dict, params: dict, except_response_model: T | None
    ) -> T | dict:
        if method in self._post_methods:
            res = self._session.post(
                self.based_url + "/" + method, params=params, data=data
            )
        elif method in self._get_methods:
            res = self._session.get(self.based_url + "/" + method, params=params)
        else:
            raise VkApiError("Could not find method:", method)
        print(res.text)

        try:
            res_json: dict = res.json()
            if except_response_model is not None:
                return Type[except_response_model](**res_json).model_dump()
            return res_json
        except TypeError:
            return ErrorResponseModel(**res_json).model_dump()
        except pydantic.ValidationError as e:
            raise VkApiError("Could not get data from JSON, because:\n", e)
        except Exception as e:
            raise VkApiError("Unknown error, I could not get JSON from response:\n", e)
