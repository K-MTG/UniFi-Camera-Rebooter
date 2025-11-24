import time
import urllib.parse
import urllib3

import requests

# Disable warnings for unverified HTTPS requests
urllib3.disable_warnings()


class CameraError(Exception):
    pass


class AuthenticationError(CameraError):
    pass


class Camera:
    def __init__(self, ip_address: str, username: str, password: str):
        self.base_url = f"https://{ip_address}"
        self.username = username
        self.password = password
        self.verify_ssl = False

        self._session = requests.Session()

    # ------------------------------------------------------
    # Cookie helpers
    # ------------------------------------------------------
    def _get_auth_cookie(self):
        """Return the authId cookie if present."""
        for c in self._session.cookies:
            if c.name == "authId":
                return c
        return None

    def _is_cookie_expired(self) -> bool:
        """Check cookie expiration using its 'expires' attribute."""
        c = self._get_auth_cookie()
        if not c or not c.expires:
            return True
        return time.time() > c.expires

    # ------------------------------------------------------
    # Login
    # ------------------------------------------------------
    def _login(self) -> None:
        url = urllib.parse.urljoin(self.base_url, "/api/1.1/login")

        resp = self._session.post(
            url,
            json={"username": self.username, "password": self.password},
            verify=self.verify_ssl,
            timeout=15
        )

        if not resp.ok:
            raise AuthenticationError(
                f"Camera login failed: {resp.status_code} {resp.text}"
            )

        # Ensure cookie was actually set
        if not self._get_auth_cookie():
            raise AuthenticationError("Camera login succeeded but no authId cookie received.")

    # ------------------------------------------------------
    # Ensure valid login
    # ------------------------------------------------------
    def _ensure_login(self):
        if self._is_cookie_expired():
            self._login()

    # ------------------------------------------------------
    # Request wrapper with auto-relogin on 401
    # ------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        self._ensure_login()

        url = urllib.parse.urljoin(self.base_url, path)
        resp = self._session.request(method, url, verify=self.verify_ssl, timeout=15, **kwargs)

        if resp.status_code == 401:
            # Try login once — prevents infinite loops
            self._login()
            resp = self._session.request(method, url, verify=self.verify_ssl, timeout=15, **kwargs)

        return resp

    # ------------------------------------------------------
    # Public API
    # ------------------------------------------------------
    def reboot(self) -> bool:
        try:
            self._request("POST", "/api/1.1/reboot")
        except requests.exceptions.ConnectionError:
            return True
        return True
