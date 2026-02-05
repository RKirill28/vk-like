from pathlib import Path
import requests
import json

from requests.cookies import RequestsCookieJar

from auth import AuthData, Authorization
from config import cfg


def get_owner_id(group_slug: str, client_id: int, access_token: str) -> int:
    res = requests.post(
        f"https://api.vk.com/method/utils.resolveScreenName?v=5.269&client_id={client_id}",
        data={"screen_name": group_slug, "access_token": access_token},
    )
    try:
        return res.json()["response"]["object_id"]
    except:
        return


def build_cookies(auth_cookies: dict) -> dict:
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
    return cookie_builder.get_dict()


def main():
    if not cfg.session_path.exists():
        cfg.session_path.parent.mkdir(parents=True, exist_ok=True)
        with cfg.session_path.open("w") as f:
            f.write("{}")

    auth_service = Authorization()
    auth_data = auth_service.run()

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

    group_slug = input("Enter the group_slug: ")
    owner_id = get_owner_id(
        group_slug, client_id=auth_data.client_id, access_token=auth_data.access_token
    )
    if not owner_id:
        print("Did not get owner_id.")
        return

    data = {
        "extended": "1",
        "fields": "photo_100,photo_200,photo_base,sex,friend_status,first_name_gen,last_name_gen,screen_name,verified,image_status,has_unseen_stories,is_government_organization,trust_mark,is_verified,social_button_type,url,is_member,can_write_private_message,can_message,member_status",
        "filters": "post",
        "filter": "owner",
        "domain": "-" + str(owner_id),
        "start_from": "0",
        "count": "1",
        "access_token": auth_data.access_token,
    }
    res = requests.post(
        f"https://api.vk.com/method/wall.get?v=5.269&client_id={auth_data.client_id}",
        data=data,
        cookies=build_cookies(auth_data.cookies),
        headers=headers,
    )
    try:
        with open("res.json", "w", encoding="utf-8") as f:
            json.dump(res.json(), f, indent=4, ensure_ascii=False)
    except:
        print("No JSON")

    print(res.text)


if __name__ == "__main__":
    main()
