from dataclasses import asdict
from pathlib import Path
import requests
import json

from requests.cookies import RequestsCookieJar

from auth import AuthData, Authorization
from captcha import CaptchaSolverService
from config import cfg
from liker import VkLiker
from models import PostsResponseModel, ErrorModel
from post_parser import PostParserService
from vk_api import VkApi


def get_owner_id(group_slug: str, client_id: int, access_token: str) -> int:
    res = requests.post(
        f"https://api.vk.com/method/utils.resolveScreenName?v=5.269&client_id={client_id}",
        data={"screen_name": group_slug, "access_token": access_token},
    )
    try:
        return res.json()["response"]["object_id"]
    except:
        return


def build_cookies(auth_cookies: list[dict]) -> RequestsCookieJar:
    cookie_builder = RequestsCookieJar()
    for cookie in auth_cookies:
        try:
            if cookie.get("sameSite"):
                cookie.pop("sameSite")

            if cookie.get("expiry"):
                cookie.pop("expiry")

            if cookie.get("httpOnly"):
                cookie.pop("httpOnly")

            cookie_builder.set(**cookie)
        except:
            pass
    return cookie_builder


def main():
    if not cfg.session_path.exists():
        cfg.session_path.parent.mkdir(parents=True, exist_ok=True)
        with cfg.session_path.open("w") as f:
            f.write("{}")

    auth_service = Authorization()
    session = auth_service.run()
    print("[+] Authorized")

    # cookie example
    # "domain": ".vk.com",
    #    "expiry": 1770292504,
    #    "httpOnly": false,
    #    "name": "remixmsts",
    #    "path": "/",
    #    "sameSite": "None",
    #    "secure": true,
    #    "value":kk
    headers = {
        "accept": "*/*",
        "accept-language": "ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "dnt": "1",
        "origin": "https://vk.com",
        "priority": "u=1, i",
        "referer": "https://vk.com/",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    }

    group_slug = input("Enter the group_slug: ").strip()
    owner_id = get_owner_id(
        group_slug, client_id=session.client_id, access_token=session.access_token
    )
    if not owner_id:
        print("Did not get owner_id.")
        return

    data = {
        "extended": "1",
        # "fields": "photo_100,photo_200,photo_base,sex,friend_status,first_name_gen,last_name_gen,screen_name,verified,image_status,has_unseen_stories,is_government_organization,trust_mark,is_verified,social_button_type,url,is_member,can_write_private_message,can_message,member_status",
        "filters": "post",
        "filter": "owner",
        "domain": "-" + str(owner_id),
        "start_from": "0",
        "count": "5",
        "access_token": session.access_token,
    }
    requests_session = requests.Session()
    requests_session.headers = headers
    requests_session.cookies = build_cookies(session.cookies)

    api = VkApi(requests_session, session)
    res = api.fetch_and_get_result(
        result_model=PostsResponseModel,
        method="wall.get",
        params={"v": "5.269", "client_id": session.client_id},
        data=data,
    )
    if isinstance(res, ErrorModel):
        print(res.error_msg)
    else:
        for item in res.items:
            print(item)

    return

    total_count_posts: int = posts_json["response"]["count"]

    for count_posts in range(0, total_count_posts, 100):
        data["start_from"] = str(count_posts)
        print("Start from", count_posts)

        res = requests.post(
            f"https://api.vk.com/method/wall.get?v=5.269&client_id={session.client_id}",
            data=data,
            cookies=build_cookies(session.cookies),
            headers=headers,
        )
        posts_json = res.json()
        post_parser_service = PostParserService(posts_json)
        posts = post_parser_service.run()

        captcha_solver = CaptchaSolverService()
        liker_service = VkLiker(session, captcha_solver)

        print(liker_service.like_posts(posts))

    # try:
    #     with open("res.json", "w", encoding="utf-8") as f:
    #         json.dump([asdict(post) for post in posts], f, indent=4, ensure_ascii=False)
    # except:
    #     print("No JSON")


if __name__ == "__main__":
    main()
