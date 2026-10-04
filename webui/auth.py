"""Authentication, Rate-Limiting, Tier Quota & Concurrency Guard for ZeroTTS.

Provides:
- Master Key (Owner / Bash CLI) with Unlimited Quota & Priority.
- VIP Keys (Custom expiry, quota, max chars).
- Guest Tier (Strict rate limit, max 200 chars, Semaphore queue).
- In-memory IP Rate Limiter & Concurrency Semaphore(1).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_HERE = Path(__file__).parent.resolve()
_ROOT = _HERE.parent.resolve()
_DATA_DIR = _ROOT / "data"
_AUTH_FILE = _DATA_DIR / "auth_keys.json"


@dataclass
class KeyRecord:
    key: str
    name: str
    tier: str  # "master" | "vip"
    max_chars: int = 50000
    hourly_limit: int = 999999
    priority: int = 10
    created_at: str = ""
    expires_at: Optional[str] = None
    total_used: int = 0
    last_used: str = ""
    is_active: bool = True


@dataclass
class AuthContext:
    tier: str  # "master" | "vip" | "guest"
    name: str
    token: Optional[str]
    max_chars: int
    hourly_limit: int
    remaining_quota: int
    priority: int
    is_master: bool
    is_vip: bool


class AuthManager:
    """Manages API Keys, Quotas, Rate Limiting, and Concurrency."""

    def __init__(self, auth_file: Path = _AUTH_FILE):
        self.auth_file = auth_file
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        self.keys: Dict[str, KeyRecord] = {}
        # Concurrency semaphore for ONNX inference (1 core CPU -> 1 concurrent task)
        self.inference_semaphore = asyncio.Semaphore(1)
        # IP / Token request timestamp tracking for rate limiting {identifier: [timestamp, ...]}
        self._request_history: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self.load_keys()

    def load_keys(self) -> None:
        """Load API keys from JSON file. Auto-initialize master key if file empty."""
        if not self.auth_file.exists():
            self._init_default_keys()
            return

        try:
            with open(self.auth_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.keys = {}
            for k, v in data.get("keys", {}).items():
                self.keys[k] = KeyRecord(**v)
        except Exception as e:
            print(f"[Auth] ⚠️ Error loading {self.auth_file}: {e}, reinitializing...")
            self._init_default_keys()

    def save_keys(self) -> None:
        """Persist keys to JSON file."""
        data = {
            "version": 1,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "keys": {k: asdict(v) for k, v in self.keys.items()},
        }
        with open(self.auth_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _init_default_keys(self) -> None:
        """Create a default master key on first startup."""
        default_master_key = f"zk_master_{secrets.token_hex(12)}"
        self.keys = {
            default_master_key: KeyRecord(
                key=default_master_key,
                name="Admin (Chính chủ)",
                tier="master",
                max_chars=100000,
                hourly_limit=999999,
                priority=10,
                created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                is_active=True,
            )
        }
        self.save_keys()
        print("\n" + "=" * 60)
        print(f"[Auth] 🔑 ĐÃ TẠO MASTER KEY MẶC ĐỊNH:")
        print(f"       Token: {default_master_key}")
        print(f"       Lưu tại: {self.auth_file}")
        print("=" * 60 + "\n")

    def create_key(
        self,
        name: str,
        tier: str = "vip",
        max_chars: int = 2000,
        hourly_limit: int = 50,
        days_valid: Optional[int] = None,
        custom_key: Optional[str] = None,
    ) -> KeyRecord:
        """Create a new API Key (Master or VIP)."""
        tier = tier.lower()
        if tier not in ("master", "vip"):
            tier = "vip"

        if custom_key:
            key = custom_key
        else:
            prefix = "zk_master_" if tier == "master" else "zk_vip_"
            key = f"{prefix}{secrets.token_hex(10)}"

        expires_at = None
        if days_valid and days_valid > 0:
            exp_ts = time.time() + (days_valid * 86400)
            expires_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp_ts))

        if tier == "master":
            max_chars = 100000
            hourly_limit = 999999
            priority = 10
        else:
            priority = 5

        record = KeyRecord(
            key=key,
            name=name,
            tier=tier,
            max_chars=max_chars,
            hourly_limit=hourly_limit,
            priority=priority,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            expires_at=expires_at,
            is_active=True,
        )
        self.keys[key] = record
        self.save_keys()
        return record

    def revoke_key(self, key: str) -> bool:
        """Deactivate or remove a key."""
        if key in self.keys:
            self.keys[key].is_active = False
            self.save_keys()
            return True
        return False

    def delete_key(self, key: str) -> bool:
        """Permanently delete a key."""
        if key in self.keys:
            del self.keys[key]
            self.save_keys()
            return True
        return False

    def list_keys(self) -> List[KeyRecord]:
        """Return list of all keys."""
        return list(self.keys.values())

    def verify_token(self, token: Optional[str], client_ip: str = "127.0.0.1") -> AuthContext:
        """Verify provided token or fallback to Guest Tier."""
        token = (token or "").strip()
        now = time.time()

        # 1. Check Master / VIP Token
        if token and token in self.keys:
            rec = self.keys[token]
            if rec.is_active:
                # Check expiration
                if rec.expires_at:
                    try:
                        exp_ts = time.mktime(time.strptime(rec.expires_at, "%Y-%m-%d %H:%M:%S"))
                        if now > exp_ts:
                            rec.is_active = False
                            self.save_keys()
                            return self._get_guest_context(client_ip, error="Token đã hết hạn.")
                    except Exception:
                        pass

                # Check hourly rate limit
                used_in_hour = self._get_recent_requests(token, window_sec=3600)
                remaining = max(0, rec.hourly_limit - len(used_in_hour))

                return AuthContext(
                    tier=rec.tier,
                    name=rec.name,
                    token=token,
                    max_chars=rec.max_chars,
                    hourly_limit=rec.hourly_limit,
                    remaining_quota=remaining,
                    priority=rec.priority,
                    is_master=(rec.tier == "master"),
                    is_vip=(rec.tier in ("master", "vip")),
                )

        # 2. Fallback to Guest
        return self._get_guest_context(client_ip)

    def _get_guest_context(self, client_ip: str, error: Optional[str] = None) -> AuthContext:
        """Guest tier parameters: max 200 chars, 5 requests / hour."""
        GUEST_MAX_CHARS = 200
        GUEST_HOURLY_LIMIT = 6

        used_in_hour = self._get_recent_requests(f"ip:{client_ip}", window_sec=3600)
        remaining = max(0, GUEST_HOURLY_LIMIT - len(used_in_hour))

        return AuthContext(
            tier="guest",
            name="Khách trải nghiệm",
            token=None,
            max_chars=GUEST_MAX_CHARS,
            hourly_limit=GUEST_HOURLY_LIMIT,
            remaining_quota=remaining,
            priority=1,
            is_master=False,
            is_vip=False,
        )

    def _get_recent_requests(self, identifier: str, window_sec: float = 3600) -> List[float]:
        now = time.time()
        timestamps = self._request_history.get(identifier, [])
        valid = [ts for ts in timestamps if (now - ts) < window_sec]
        self._request_history[identifier] = valid
        return valid

    def record_usage(self, auth: AuthContext, text_len: int, client_ip: str = "127.0.0.1") -> None:
        """Record usage and update counters."""
        now = time.time()
        identifier = auth.token if auth.token else f"ip:{client_ip}"
        
        if identifier not in self._request_history:
            self._request_history[identifier] = []
        self._request_history[identifier].append(now)

        if auth.token and auth.token in self.keys:
            rec = self.keys[auth.token]
            rec.total_used += 1
            rec.last_used = time.strftime("%Y-%m-%d %H:%M:%S")
            self.save_keys()


# Global Singleton Instance
auth_manager = AuthManager()
