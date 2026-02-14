import json
from json.decoder import WHITESPACE
from typing import Generic, TypeVar, Type, Literal
from pprint import pprint

import pydantic
import requests
from pydantic import BaseModel

from auth import AuthData
from models import (
    ErrorModel,
    ErrorResponseModel,
    AddLikeModel,
    PostModel,
    PostsResponseModel,
)

T = TypeVar("T", bound=BaseModel)


class VkApiError(Exception):
    """Ошибка в работе VkApi"""

    def __init__(self, error: ErrorModel | str):
        self.error = error
        if isinstance(error, ErrorModel):
            super().__init__(f'API VK ERROR CODE: {error.error_code}, ERROR MSG: {error.error_msg} ')
        else:
            super().__init__(error)

class VkApi:
    based_url = "https://api.vk.com/method"

    def __init__(self, request_session: requests.Session):
        self._session = request_session

    def fetch_and_get_result(
        self, result_model: Type[T], method: str, params: dict, data: dict | None = None
    ) -> T | ErrorModel:
        res = self._session.post(
            self.based_url + "/" + method, params=params, data=data
        )
        return self._parse_response(res, result_model)

    def _parse_response(
        self, response: requests.Response, model: Type[T]
    ) -> T | ErrorModel:
        try:
            assert response.status_code == 200
            res_json = response.json()
            if res_json.get("error") is not None:
                error_data = ErrorModel.model_validate(res_json["error"])
                raise VkApiError(error_data)

            if res_json.get("response"):
                return model.model_validate(res_json["response"])
            else:
                return model.model_validate(res_json)
        except json.JSONDecodeError as e:
            raise VkApiError(
                f"Could not get JSON from response: {response.text}\nError: {str(e)}"
            )
        except pydantic.ValidationError as e:
            raise VkApiError(
                f"Could not create ErrorModel\nResponse: {response.text}\nValidateError: {str(e)}"
            )
        except Exception as e:
            raise VkApiError(
                f"Could not get response, status_code: {response.status_code}\nError: {e}"
            )
