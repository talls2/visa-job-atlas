"""HTTP helpers: stdlib urllib with retries, plus a Windows curl fallback.

Some government sites (e.g. ind.nl) serve an incomplete TLS chain that
Python's OpenSSL cannot verify, while Windows' Schannel (used by curl.exe)
fetches the missing intermediate itself. Verification is never disabled.
"""

import json
import os
import shutil
import ssl
import subprocess
import time
import urllib.error
import urllib.request

# Generic browser user-agents get bot-challenged by some portals (open.canada.ca);
# an honest identifier is accepted everywhere tested.
USER_AGENT = "visa-job-atlas/1.0 (+https://github.com/talls2/visa-job-atlas; open-source job research)"

_CURL = shutil.which("curl.exe") or shutil.which("curl") or (
    r"C:\Windows\System32\curl.exe" if os.path.exists(r"C:\Windows\System32\curl.exe") else None
)


class FetchError(Exception):
    pass


def _curl(url, headers, timeout):
    if not _CURL:
        raise FetchError("curl.exe not available for TLS fallback")
    cmd = [_CURL, "-sSL", "--fail", "--max-time", str(timeout), "-A", USER_AGENT]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise FetchError(f"curl failed ({proc.returncode}) for {url}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def fetch(url, headers=None, timeout=60, retries=2, data=None):
    """Return the response body as bytes. Raises FetchError on failure.
    `data` (dict) sends a JSON POST instead of a GET."""
    headers = dict(headers or {})
    headers.setdefault("User-Agent", USER_AGENT)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers, data=body)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            # 4xx other than 429 will not get better by retrying.
            if e.code != 429 and 400 <= e.code < 500:
                raise FetchError(f"HTTP {e.code} for {url}") from e
            last = e
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLCertVerificationError):
                return _curl(url, {k: v for k, v in headers.items() if k != "User-Agent"}, timeout)
            last = e
        except (TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise FetchError(f"giving up on {url}: {last}")


def fetch_json(url, headers=None, timeout=60, data=None):
    body = fetch(url, headers=headers, timeout=timeout, data=data)
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise FetchError(f"non-JSON response from {url}: {body[:120]!r}") from e


def fetch_text(url, headers=None, timeout=60, encoding="utf-8"):
    return fetch(url, headers=headers, timeout=timeout).decode(encoding, "replace")
