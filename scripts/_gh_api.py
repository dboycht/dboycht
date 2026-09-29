"""
Shared GitHub API helper for the chart scripts.

Why this exists: the chart scripts used to call urllib directly with no
timeout, no retry and no response validation. A single transient API error
(reset connection / 5xx / secondary rate limit) raised an uncaught exception,
killed the step with exit code 1 and skipped the commit step, losing that
day's chart updates. See update 2026-09-27 in the repo's Actions history.
"""
import json
import os
import time
import urllib.error
import urllib.request

API_ROOT = "https://api.github.com"
USER_AGENT = "dboycht-readme"
TIMEOUT = 30          # seconds per request
RETRIES = 3           # total attempts
BACKOFF = 2           # seconds, doubled per retry: 2s, 4s

# Permanent errors: retrying cannot help, fail fast with a clear message.
FATAL_STATUS = {400, 401, 404, 422}


def fetch_json(path, token=None, retries=RETRIES, timeout=TIMEOUT):
    """GET a GitHub API path and return the parsed JSON list.

    Retries transient failures (connection errors, timeouts, 5xx, 403/429
    rate limits) with exponential backoff. Exits non-zero with a readable
    message instead of dumping a traceback that says nothing.
    """
    url = path if path.startswith("http") else API_ROOT + path
    token = token or os.environ.get("GITHUB_TOKEN")
    last_error = None

    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
        )
        if token:
            req.add_header("Authorization", f"token {token}")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code} {exc.reason}"
            if exc.code in FATAL_STATUS:
                raise SystemExit(f"[gh-api] {url} -> {last_error} (not retryable)")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = repr(exc)
        else:
            if not isinstance(data, list):
                # An error payload (dict) would otherwise be iterated as keys
                # further down and blow up with a confusing TypeError.
                raise SystemExit(f"[gh-api] {url} -> expected a JSON list, got {type(data).__name__}")
            return data

        if attempt < retries:
            wait = BACKOFF ** attempt
            print(f"[gh-api] attempt {attempt}/{retries} failed ({last_error}), retrying in {wait}s", flush=True)
            time.sleep(wait)

    raise SystemExit(f"[gh-api] giving up after {retries} attempts: {url} -> {last_error}")
