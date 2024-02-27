import argparse
from dataclasses import dataclass
from typing import Tuple
from urllib.parse import parse_qs, urlparse

import cv2
import httpx
from rich import print
from rich.progress import Progress


def read_qr_img(img_path: str) -> str:
    img = cv2.imread(img_path)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data


@dataclass
class OktaVerifyData:
    t: str
    f: str
    domain: str


def get_domain_key(domain: str) -> Tuple[str, str]:
    url = f"https://{domain}.okta.com/oauth2/v1/keys"
    response = httpx.get(url)
    response.raise_for_status()
    data = response.json()
    return data["keys"][0]["kid"], data["keys"][0]["n"]


def create_okta_authenticator(
    device_name: str, verify_data: OktaVerifyData, kid: str, n: str
):
    # inspo: https://gist.github.com/kamilhism/9f6f26ce3e10b6685af8c43f33aca808
    url = f"https://{verify_data.domain}.okta.com/idp/authenticators"
    headers = {
        "Authorization": f"OTDT {verify_data.t}",
        "User-Agent": "D2DD7D3915.com.okta.android.auth/6.8.1 DeviceSDK/0.19.0 Android/7.1.1 unknown/Google",
    }
    data = {
        "authenticatorId": verify_data.f,
        "device": {
            "clientInstanceBundleId": "com.okta.android.auth",
            "clientInstanceDeviceSdkVersion": "DeviceSDK 0.19.0",
            "clientInstanceVersion": "6.8.1",
            "clientInstanceKey": {
                "alg": "RS256",
                "e": "AQAB\n",
                "okta:isFipsCompliant": False,
                "okta:kpr": "SOFTWARE",
                "kty": "RSA",
                "use": "sig",
                "kid": kid,
                "n": n,
            },
            "deviceAttestation": {},
            "displayName": device_name,
            "fullDiskEncryption": False,
            "isHardwareProtectionEnabled": False,
            "manufacturer": "unknown",
            "model": "Google",
            "osVersion": "25",
            "platform": "ANDROID",
            "rootPrivileges": True,
            "screenLock": False,
            "secureHardwarePresent": False,
        },
        "key": "okta_verify",
        "methods": [
            {"isFipsCompliant": False, "supportUserVerification": False, "type": "totp"}
        ],
    }
    response = httpx.post(url, headers=headers, json=data)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("[red bold]Invalid token ... it may have expired[/]")
            exit(1)
    return response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode QR code from image")
    parser.add_argument("img_path", help="path to the image")
    args = parser.parse_args()

    print(
        "[red bold]Read the code before proceeding! You are dealing with authentication data. Take it seriously.[/]"
    )

    with Progress() as progress:
        task = progress.add_task("Reading QR code", total=None)
        data = read_qr_img(args.img_path)
        progress.remove_task(task)

    url = urlparse(data)
    qs = parse_qs(url.query)

    device_name = input("Enter a display name (e.g. 1password)\n> ")

    verify_data = OktaVerifyData(
        t=qs["t"][0],
        f=qs["f"][0],
        domain=urlparse(qs["s"][0]).netloc.replace(".okta.com", ""),
    )
    kid, n = get_domain_key(verify_data.domain)
    res = create_okta_authenticator(device_name, verify_data, kid, n)
    print(f"Your TOTP secret is: [green]{res['methods'][0]['sharedSecret']}[/]")
    print(
        "\n\nAdd this to your TOTP manager.\nYou can now use the 'enter a code' authentication method on the Okta authenticate screen."
    )
