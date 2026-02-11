# For make like to post:

# class: PostBottomAction PostBottomAction--transparent PostButtonReactions PostButtonReactions--post
# data-reaction-target-object="wall-200615136_10604" (from HTML)
# data-reaction-hash="053250036fc8e57d33" (from HTML)

# class: feed_row > post-...
# data-post-track-code="a343659epJjP3YGULfYpihv3j0-IkHOqlrg0OncQrLUajOtsjoqBkPy_saEamTzdsnUPhbimScvC6GdRM0flvxzhih7l7w"

# Get authorizate > get cookies > get group page(all posts) > make likes

from datetime import datetime
import requests
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc

import json

from dataclasses import asdict, dataclass
from config import cfg


localeStorageParse = """

let stor = localStorage;

let parsed = {};
for (i = 0; i <= stor.lenght; i++) {
    if stor.key(i) === null {
        break;
    }
    else {
        let key = stor.key(i);
        parsed[key] = stor.getItem(key);
    }
}
return parsed;

"""


class AuthorizationServiceError(Exception):
    """Ошибка в работе сервиса авторизации"""


@dataclass
class AuthData:
    access_token: str
    client_id: int
    expires: int
    cookies: list[dict]


class Authorization:
    """
    Класс для авторизации пользователя в вк.
    Использует имитацию браузера через undetected-chromedriver.
    Задача - получить cookies и local storge,
    откуда потом выудить access_token, client_id и app_version для послседующих запросов.
    """

    MOBILE_PHONE_XPATH = "/html/body/div[4]/div[2]/div[2]/div/div[3]/div[1]/div/div/div/div/div[1]/div/div/div[2]/div[1]/div/div/div/form/div[1]/div[3]/span/div/div[2]/input"

    def __init__(self) -> None:
        self._vk_auth_url = "https://vk.com"
        self._opts = uc.ChromeOptions()
        # self._opts.add_argument("--no-sandbox")
        # self._opts.add_argument("--disable-dev-shm-usage")
        self._driver = uc.Chrome(
            version_main=144,
            # options=self._opts,
            # driver_executable_path="./chromedriver",
        )

    def end(self) -> None:
        self._driver.close()
        self._driver.quit()

    def _get_local_storage(self) -> dict:
        local_storage = self._driver.execute_script("return localStorage;")
        for k, v in local_storage.items():
            if isinstance(v, str):
                try:
                    local_storage[k] = json.loads(v)
                except:
                    pass
        print("[*] Got local storage from browser")
        return local_storage

    def _parse_access_token(self, data: dict) -> tuple[int, str, int]:
        for k, v in data.items():
            if "web_token:login:auth" in k:
                client_id = int(k.split(":")[0])
                access_token = v["access_token"]
                expires = int(v["expires"])
                print("[*] Parsed auth data from localStorage")

                return client_id, access_token, expires

        raise AuthorizationServiceError(
            "Не смог получить client_id, access_token, expires"
        )

    def _get_auth_page(self) -> None:
        self._driver.get(self._vk_auth_url)

        input("[+] Press ENTER when you log in in to your account...")

    def _save_auth_session(self, auth: AuthData) -> None:
        with cfg.session_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(auth), f, indent=4, ensure_ascii=False)
        print("[*] Saved auth session")

    def _get_auth_session(self) -> AuthData | None:
        try:
            with cfg.session_path.open("r", encoding="utf-8") as f:
                session = json.load(f)
            res = AuthData(**session)
            print("[*] Got auth session")
            return res
        except:
            return

    def _check_session(self, session: AuthData) -> bool:
        if datetime.now().timestamp() >= session.expires:
            print("[*] Check session: Session expired")
            return False
        print("[*] Check session: Session did not expire")
        return True

    def _get_new_acces_token(self, auth: AuthData) -> AuthData:
        res = requests.post(
            "https://login.vk.com/?act=web_token",
            data={"access_token": auth.access_token, "app_id": auth.client_id},
        )
        try:
            new_auth = res.json()
            print("[*] Updated auth data")
            return AuthData(
                access_token=new_auth["access_token"],
                client_id=auth.client_id,
                expires=new_auth["expires"],
                cookies=auth.cookies,
            )
        except KeyError:
            raise AuthorizationServiceError(
                "Не могу получить из JSON нужные данные, при обновлении токена!"
            )
        except json.JSONDecodeError:
            raise AuthorizationServiceError(
                "Не могу получить JSON при обновлении токена!"
            )

    def update_session(self, auth: AuthData) -> AuthData:
        new_auth = self._get_new_acces_token(auth)
        self._save_auth_session(new_auth)
        print("[*] Updated auth session.")
        return new_auth

    def run(self) -> AuthData:
        try:
            session = self._get_auth_session()
            if session:
                if self._check_session(session):
                    return session

            self._get_auth_page()
            WebDriverWait(self._driver, 300).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            local_storage = self._get_local_storage()
            auth_data = self._parse_access_token(local_storage)
            session = AuthData(
                auth_data[1], auth_data[0], auth_data[2], self._driver.get_cookies()
            )
            self._save_auth_session(session)

            return session
        finally:
            self.end()


if __name__ == "__main__":
    auth = Authorization()
    r = auth.run()
    # with open("test.json", "w", encoding="utf-8") as f:
    #     json.dump(r, f, ensure_ascii=False, indent=4)
