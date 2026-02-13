from dataclasses import dataclass

from vk_api import VkApi


class PostParserServiceError(Exception):
    """Ошибка в работе парсера постов"""


@dataclass(frozen=True)
class Post:
    id: int
    track_code: str
    likes_count: int
    type: str
    owner_id: int
    text: str


class PostParserService:
    def __init__(self, api: VkApi, posts: dict) -> None:
        """
                Параметры
                posts: Словарь с постами вида:
        ```Json
                {
                    "response": {
                        "count": ...,
                        items: [...]
                    }
                }
        ```

        """
        self._posts = posts
        if res := self._posts.get("response"):
            if posts := res.get("items"):
                self._posts = posts
        else:
            raise PostParserServiceError(
                'Ошибка при попытке получить список постов из JSON. Требуется передать словарь вида: {"response": {"count": ..., items: [...]}}'
            )

    def _parse_post(self, post: dict) -> dict:
        try:
            res = {
                "id": post["id"],
                "track_code": post["track_code"],
                "likes_count": post["likes"]["count"],
                "type": post["type"],
                "owner_id": post["owner_id"],
                "text": post["text"].strip(),
            }
            print(f"[*] Parsed post post_id={post['id']}")
            return res
        except KeyError as e:
            raise PostParserServiceError(f"Не удалось получить ключ из поста: {e}")

    def run(self) -> list[Post]:
        posts = []
        for item in self._posts:
            post = self._parse_post(item)
            if post:
                posts.append(Post(**post))

        return posts
