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
    def __init__(self, captcha_solver: CaptchaSolverService):
        self._captcha_solver = captcha_solver

    def _like_post(self, client_id: int, access_token: str, post: Post) -> None:
        res = requests.post(
            "https://api.vk.com/method/likes.add",
            params={"v": "5.269", "client_id": client_id},
            data={
                "type": post.type,
                "owner_id": post.owner_id,
                "item_id": post.id,
                "track_code": post.track_code,
                "ref": "group",  # WARN: or not group???
                "reaction_id": 0,  # for like reaction
                "access_token": access_token,
            },
        )
        if res.status_code != 200:
            raise VkLikerServiceError(
                f"Не удалось успешно выполнить запрос на добавление лайка:\n{res.text}"
            )

        try:
            self._check_like(res.json())
            print(f"[+] Liked post: https://vk.com/wall{post.owner_id}_{post.id}")
        except json.JSONDecodeError:
            raise VkLikerServiceError(
                f"Не удалось получить JSON в ответ от ВК API:\n{res.text}"
            )

    def _check_like(self, data: dict) -> None:
        error: dict | None = data.get("error")
        if error is not None:
            if error.get("error_code") == 14:
                print(f"[!] Captcha needed, captcha_sid:{error.get('captcha_sid')}")
                self._captcha_solver.solve(data)
            else:
                print(f"[!] Got unknown error: {error.get('error_msg')}")

    def like_posts(self, posts: list[Post], session: AuthData) -> list[str]:
        """
        Лайкает переданные посты.
        Возвращает ссылки на посты, которые удалось пролайкать.
        """
        liked_post_links = []
        count = 0
        for post in posts:
            try:
                if count == random.randrange(5, 8):
                    time.sleep(random.randrange(2, 5))
                    count = 0
                else:
                    time.sleep(random.randrange(1, 3))

                self._like_post(session.client_id, session.access_token, post)
                liked_post_links.append(f"https://vk.com/wall{post.owner_id}_{post.id}")
                count += 1
            except Exception as err:
                print(
                    f"[*] Did not like the post https://vk.com/wall{post.owner_id}_{post.id}, because:\n",
                    err,
                )
        return liked_post_links
