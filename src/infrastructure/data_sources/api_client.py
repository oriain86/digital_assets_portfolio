
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Base API client with rate limiting and retry logic."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds

        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request with retry logic."""
        self._rate_limit()

        url = f"{self.base_url}/{endpoint}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

        return {}
