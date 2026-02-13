import json

from captcha import Captcha, CaptchaSolverService
from post_parser import Post
from auth import AuthData

import requests
import random
import time


class VkLikerServiceError(Exception):
    """Ошибка в работе VkLiker сервиса"""


class VkLiker:
    def __init__(self, session: AuthData, captcha_solver: CaptchaSolverService):
        self._captcha_solver = captcha_solver

        self._data = {
            "ref": "group",  # WARN: or not group???
            "reaction_id": 0,  # for like reaction
        }
        self._session = session

    def _like_post(self, post: Post) -> None:
        res = requests.post(
            "https://api.vk.com/method/likes.add",
            params={"v": "5.269", "client_id": self._session.client_id},
            data=self._data,
        )
        if res.status_code != 200:
            raise VkLikerServiceError(
                f"Не удалось успешно выполнить запрос на добавление лайка:\n{res.text}"
            )

        try:
            self._check_like(post, res.json())
            print(f"[+] Liked post: https://vk.com/wall{post.owner_id}_{post.id}")
        except json.JSONDecodeError:
            raise VkLikerServiceError(
                f"Не удалось получить JSON в ответ от ВК API:\n{res.text}"
            )

    def _check_like(self, post: Post, data: dict) -> None:
        error: dict | None = data.get("error")
        if error is not None:
            if error.get("error_code") == 14:
                print(error)
                print(f"[!] Captcha needed, captcha_sid:{error.get('captcha_sid')}")
                self._data["success_token"] = self._captcha_solver.solve(data)
                self._like_post(post)
            else:
                print(f"[!] Got unknown error: {error.get('error_msg')}")

    def like_posts(self, posts: list[Post]) -> list[str]:
        """
        Лайкает переданные посты.
        Возвращает ссылки на посты, которые удалось пролайкать.
        """
        self._data["access_token"] = self._session.access_token
        liked_post_links = []
        count = 0
        for post in posts:
            try:
                if count == random.randrange(5, 8):
                    time.sleep(random.randrange(2, 5))
                    count = 0
                else:
                    time.sleep(random.randrange(1, 3))

                self._data["type"] = post.type
                self._data["owner_id"] = post.owner_id
                self._data["item_id"] = post.id
                self._data["track_code"] = post.track_code

                self._like_post(post)
                liked_post_links.append(f"https://vk.com/wall{post.owner_id}_{post.id}")
                count += 1
            except Exception as err:
                print(
                    f"[*] Did not like the post https://vk.com/wall{post.owner_id}_{post.id}, because:\n",
                    err,
                )
        return liked_post_links
