import hashlib
import json
import re
from dataclasses import dataclass

from urllib.parse import parse_qs, urlparse

import requests


@dataclass
class Captcha:
    redirect_uri: str
    session_token: str


class CaptchaSolverServiceError(Exception):
    """Ошибка в работае сервиса решения капчи"""


class CaptchaSolverService:
    def solve(self, data: dict):
        captcha = self._parse_captcha_json(data)
        self._captcha_settings(captcha.session_token)
        self._captcha_component_done(captcha.session_token)

        hash = self._perform_pow(captcha.redirect_uri)
        succes_token = self._captcha_check(hash, captcha.session_token)
        self._end_captcha(succes_token)

    def _calculate_hash(self, pow_input: str, diff: int = 2):
        nonce = 0
        prefix = "0" * diff
        while True:
            data = pow_input + str(nonce)
            hash: str = hashlib.sha256(data.encode("utf-8")).hexdigest()
            if hash.startswith(prefix):
                return hash
            nonce += 1

    def _get_pow_input(self, redirect_uri: str) -> str:
        res = requests.get(redirect_uri)
        html = res.text
        return re.search(r'powInput[:\s"\'=]+([A-Za-z0-9]+)', html).group(1)

    def _perform_pow(self, redirect_uri: str):
        """Script from VK, js from script tag"""
        pow_input = self._get_pow_input(redirect_uri)
        hash = self._calculate_hash(pow_input, 2)
        print(f"[*] Got captcha hash: {hash}")
        return hash

    def _parse_captcha_json(self, captcha_error: dict) -> Captcha:
        error: dict | None = captcha_error.get("error")
        if error is None:
            raise CaptchaSolverServiceError("В переданном словаре нету ключа error.")

        redirect_uri: str | None = error.get("redirect_uri")
        if redirect_uri is None:
            raise CaptchaSolverServiceError("Не смог получить redirect_uri из ошибки")
        print("[*] Got redirect_uri")

        redirect_uri_query = urlparse(redirect_uri).query
        redirect_uri_params = parse_qs(redirect_uri_query)
        session_token: str | None = redirect_uri_params.get("session_token")
        if session_token is None:
            raise CaptchaSolverServiceError(
                "Не удалось получить session_token из redirect_uri."
            )
        print("[*] Got session_token from redirect_uri")
        return Captcha(redirect_uri=redirect_uri, session_token=session_token)

    def _captcha_settings(self, session_token: str):
        res = requests.post(
            "https://api.vk.com/method/captchaNotRobot.settings",
            params={"v": "5.131"},
            data={
                "session_token": session_token,
                "domain": "vk.com",
                "adFp": "",
                "access_token": "",
            },
        )
        if res.status_code != 200:
            raise CaptchaSolverServiceError(
                f"Не удалось выполнить запрос captchaNotRobot.settings:\n{res.text}"
            )
        print(f"[*] Success made request captchaNotRobot.settings and got:\n{res.text}")

    def _captcha_component_done(self, session_token: str) -> None:
        res = requests.post(
            "https://api.vk.com/method/captchaNotRobot.componentDone",
            params={"v": "5.131"},
            data={
                "session_token": session_token,
                "domain": "vk.com",
                "adFp": "",
                "access_token": "",
                "device": {
                    "screenWidth": 1680,
                    "screenHeight": 1050,
                    "screenAvailWidth": 1680,
                    "screenAvailHeight": 1050,
                    "innerWidth": 1125,
                    "innerHeight": 936,
                    "devicePixelRatio": 1,
                    "language": "en-US",
                    "languages": ["en-US", "en"],
                    "webdriver": False,
                    "hardwareConcurrency": 4,
                    "deviceMemory": 8,
                    "connectionEffectiveType": "4g",
                    "notificationsPermission": "denied",
                },
            },
        )
        if res.status_code != 200:
            raise CaptchaSolverServiceError(
                f"Не удалось выполнить запрос captchaNotRobot.componentDone:\n{res.text}"
            )
        try:
            if res.json()["response"]["status"] == "OK":
                print(
                    f"[*] Success made request captchaNotRobot.componentDone and got:\n{res.text}"
                )
            else:
                raise CaptchaSolverServiceError(
                    f"Не удалось выполнить запрос captchaNotRobot.componentDone:\n{res.text}"
                )
        except Exception as e:
            raise CaptchaSolverServiceError(
                f"Не удалось выполнить запрос captchaNotRobot.componentDone, error:\n{e}, response text:\n{res.text}"
            )

    def _captcha_check(self, hash: str, session_token: str) -> str:
        res = requests.post(
            "https://api.vk.com/method/captchaNotRobot.check",
            params={"v": "5.131"},
            data={
                "session_token": session_token,
                "accelerometer": [],
                "gyroscope": [],
                "motion": [],
                "cursor": [
                    {"x": 864, "y": 705},
                    {"x": 496, "y": 607},
                    {"x": 469, "y": 553},
                    {"x": 476, "y": 541},
                    {"x": 476, "y": 540},
                    {"x": 810, "y": 560},
                    {"x": 1000, "y": 649},
                    {"x": 1000, "y": 649},
                    {"x": 1000, "y": 649},
                    {"x": 1000, "y": 649},
                    {"x": 1000, "y": 649},
                    {"x": 896, "y": 733},
                    {"x": 438, "y": 571},
                    {"x": 437, "y": 535},
                    {"x": 453, "y": 522},
                    {"x": 453, "y": 522},
                ],
                "taps": [],
                "connectionRtt": [
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                    200,
                ],
                "connectionDownlink": [
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                ],
                "answer": "e30=",
                "adFp": "",
                "access_token": "",
                "browser_fp": "",
                "hash": hash,
            },
        )
        if res.status_code != 200:
            raise CaptchaSolverServiceError(
                f"Не смог получить ответ на решение капчи, код статуса: {res.status_code}"
            )
        print()
        print(res.text)
        print()
        try:
            res_json = res.json()
        except json.JSONDecodeError:
            raise CaptchaSolverServiceError(
                f"Could not get JSON from response in the captcha_check function, response:{res.text}"
            )

        try:
            if res_json["response"]["status"] == "OK":
                print("[+] Success solved captcha!")
                if (success_token := res_json["response"]["success_token"]) is not None:
                    return success_token
        except KeyError as e:
            raise CaptchaSolverServiceError(
                f"Не смог получить данные из ответа на решение капчи:\n{e}, ответ от АПИ:\n{res.text}"
            )

    def _end_captcha(self, success_token: str) -> None:
        res = requests.post(
            "https://api.vk.com/method/captchaNotRobot.endSession?v=5.131",
            params={"v": "5.131"},
            data={"success_token": success_token, "domain": "vk.com"},
        )
        if res.text == '{response: {status: "OK"}}':
            print("[*] Success finished captcha")
        else:
            raise CaptchaSolverServiceError(
                f"Не удалось успешной закончить капчу:\n{res.text}"
            )


#
#
# async function calculateHash(input, nonce) {
#   const encoder = new TextEncoder();
#   const data = encoder.encode(input + nonce);
#   const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
#   const hashArray = Array.from(new Uint8Array(hashBuffer));
#   const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
#   return hashHex;
# }
#
# async function performPoW(input, difficulty) {
#   let nonce = 0;
#   let hash = '';
#
#   while (!hash.startsWith('0'.repeat(difficulty))) {
#     nonce++;
#     hash = await calculateHash(input, nonce);
#   }
#
#   // store the result in window.captchaPowResult
#   window.captchaPowResult = hash;
# }
#
# const powInput = "bI7ZS3LViYRxXCCF"; - какая та строка хер знает откуда бля
# const difficulty = 2;
# performPoW(powInput, difficulty)
