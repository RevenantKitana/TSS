"""Authentication, Rate-Limiting, 2-Tier Isolation & Storage Cleanup for ZeroTTS.

Architecture:
1. Key Users (Vĩnh viễn):
   - Any valid key configured in data/auth_keys.json.
   - Dedicated, permanent storage at outputs/keys/<storage_slug>/.
   - Immune to automated expiration cleanup.
2. Guest Users (Phiên ngắn - Ephemeral):
   - Anonymous visitors without a key.
   - Short-lived storage at outputs/ephemeral/<session_id>/.
   - Automatically pruned after 30 minutes or when exceeding quota.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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


def sanitize_slug(name: str, fallback_key: str = "") -> str:
    """Generate a clean, filesystem-safe directory slug from any name (including Vietnamese)."""
    import unicodedata
    # Normalize unicode to separate base letters from diacritics
    nfkd = unicodedata.normalize("NFKD", name.strip())
    ascii_text = nfkd.encode("ASCII", "ignore").decode("utf-8")
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", ascii_text.lower())
    slug = re.sub(r"_+", "_", slug).strip("_-")
    if not slug:
        token_hash = hashlib.sha256((fallback_key or secrets.token_hex(4)).encode("utf-8")).hexdigest()[:8]
        slug = f"key_{token_hash}"
    return slug


@dataclass
class KeyRecord:
    key: str
    name: str
    tier: str = "key"  # "key"
    storage_slug: str = ""  # Subfolder name under outputs/keys/<storage_slug>/
    max_chars: int = 100000
    hourly_limit: int = 999999
    priority: int = 10
    created_at: str = ""
    total_used: int = 0
    last_used: str = ""
    is_active: bool = True

    def __post_init__(self):
        if not self.storage_slug:
            self.storage_slug = sanitize_slug(self.name, self.key)


@dataclass
class AuthContext:
    tier: str  # "key" | "guest"
    name: str
    token: Optional[str]
    storage_slug: Optional[str]
    max_chars: int
    hourly_limit: int
    remaining_quota: int
    priority: int
    has_key: bool
    is_master: bool = False  # For backwards compatibility with UI
    is_vip: bool = False     # For backwards compatibility with UI


class AuthManager:
    """Manages API Keys, Dedicated Storage Slugs, Quotas, and Concurrency."""

    def __init__(self, auth_file: Path = _AUTH_FILE):
        self.auth_file = auth_file
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        self.keys: Dict[str, KeyRecord] = {}
        # Concurrency semaphore for ONNX inference (1 core CPU -> 1 concurrent synthesis)
        self.inference_semaphore = asyncio.Semaphore(1)
        # IP / Token request timestamp tracking for rate limiting
        self._request_history: Dict[str, List[float]] = {}
        self.load_keys()

    def load_keys(self) -> None:
        """Load API keys from JSON file. Auto-initialize default key if file is missing."""
        if not self.auth_file.exists():
            self._init_default_keys()
            return

        try:
            with open(self.auth_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.keys = {}
            for k, v in data.get("keys", {}).items():
                if "tier" not in v or v["tier"] in ("master", "vip"):
                    v["tier"] = "key"
                if "storage_slug" not in v or not v["storage_slug"]:
                    v["storage_slug"] = sanitize_slug(v.get("name", ""), k)
                # Clean up deprecated fields
                v.pop("expires_at", None)
                self.keys[k] = KeyRecord(**v)
        except Exception as e:
            print(f"[Auth] ⚠️ Error loading {self.auth_file}: {e}, reinitializing...")
            self._init_default_keys()

    def save_keys(self) -> None:
        """Persist keys to JSON file."""
        data = {
            "version": 2,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "keys": {k: asdict(v) for k, v in self.keys.items()},
        }
        with open(self.auth_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _init_default_keys(self) -> None:
        """Create a default master key on first startup."""
        default_key = f"zk_key_{secrets.token_hex(12)}"
        self.keys = {
            default_key: KeyRecord(
                key=default_key,
                name="Admin (Chính chủ)",
                tier="key",
                storage_slug="admin",
                max_chars=100000,
                hourly_limit=999999,
                priority=10,
                created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                is_active=True,
            )
        }
        self.save_keys()
        print("\n" + "=" * 60)
        print(f"[Auth] 🔑 ĐÃ KHỞI TẠO KEY MẶC ĐỊNH:")
        print(f"       Token: {default_key}")
        print(f"       Không gian: outputs/keys/admin/")
        print(f"       Lưu tại: {self.auth_file}")
        print("=" * 60 + "\n")

    def create_key(
        self,
        name: str,
        custom_key: Optional[str] = None,
        storage_slug: Optional[str] = None,
        max_chars: int = 100000,
        hourly_limit: int = 999999,
    ) -> KeyRecord:
        """Create a new permanent Key with dedicated storage."""
        name = name.strip() or "User"
        key = (custom_key or "").strip() or f"zk_key_{secrets.token_hex(10)}"
        slug = sanitize_slug(storage_slug or name, key)

        # Check for slug collision among existing keys
        existing_slugs = {v.storage_slug for k_id, v in self.keys.items() if k_id != key}
        base_slug = slug
        counter = 2
        while slug in existing_slugs:
            slug = f"{base_slug}_{counter}"
            counter += 1

        record = KeyRecord(
            key=key,
            name=name,
            tier="key",
            storage_slug=slug,
            max_chars=max_chars,
            hourly_limit=hourly_limit,
            priority=10,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            is_active=True,
        )
        self.keys[key] = record
        self.save_keys()

        # Pre-create dedicated output directory
        base_outputs = Path(os.environ.get("ZEROTTS_OUTPUT_DIR", _ROOT / "outputs"))
        (base_outputs / "keys" / slug).mkdir(parents=True, exist_ok=True)

        return record

    def set_key_status(self, key_or_name: str, is_active: bool) -> Optional[KeyRecord]:
        """Enable or disable a key."""
        record = self.find_key(key_or_name)
        if record:
            record.is_active = is_active
            self.save_keys()
            return record
        return None

    def delete_key(self, key_or_name: str, purge_storage: bool = False) -> Optional[KeyRecord]:
        """Permanently delete a key, optionally deleting its storage directory."""
        record = self.find_key(key_or_name)
        if record:
            del self.keys[record.key]
            self.save_keys()
            if purge_storage and record.storage_slug:
                base_outputs = Path(os.environ.get("ZEROTTS_OUTPUT_DIR", _ROOT / "outputs"))
                key_dir = base_outputs / "keys" / record.storage_slug
                if key_dir.is_dir():
                    shutil.rmtree(key_dir, ignore_errors=True)
            return record
        return None

    def find_key(self, key_or_name: str) -> Optional[KeyRecord]:
        """Find key record by exact key token, storage slug, or name."""
        target = (key_or_name or "").strip()
        if not target:
            return None
        if target in self.keys:
            return self.keys[target]
        for rec in self.keys.values():
            if rec.name.lower() == target.lower() or rec.storage_slug.lower() == target.lower():
                return rec
        return None

    def list_keys(self) -> List[KeyRecord]:
        """Return list of all registered keys."""
        return list(self.keys.values())

    def verify_token(self, token: Optional[str], client_ip: str = "127.0.0.1") -> AuthContext:
        """Verify provided token or fallback to Guest Tier."""
        token = (token or "").strip()

        # 1. Check Key in Database
        if token and token in self.keys:
            rec = self.keys[token]
            if rec.is_active:
                used_in_hour = self._get_recent_requests(token, window_sec=3600)
                remaining = max(0, rec.hourly_limit - len(used_in_hour))

                return AuthContext(
                    tier="key",
                    name=rec.name,
                    token=token,
                    storage_slug=rec.storage_slug,
                    max_chars=rec.max_chars,
                    hourly_limit=rec.hourly_limit,
                    remaining_quota=remaining,
                    priority=rec.priority,
                    has_key=True,
                    is_master=True,
                    is_vip=True,
                )

        # 2. Fallback to Guest
        return self._get_guest_context(client_ip)

    def _get_guest_context(self, client_ip: str) -> AuthContext:
        """Guest tier parameters: max 200 chars, 6 requests / hour."""
        GUEST_MAX_CHARS = 200
        GUEST_HOURLY_LIMIT = 6

        used_in_hour = self._get_recent_requests(f"ip:{client_ip}", window_sec=3600)
        remaining = max(0, GUEST_HOURLY_LIMIT - len(used_in_hour))

        return AuthContext(
            tier="guest",
            name="Khách vãng lai",
            token=None,
            storage_slug=None,
            max_chars=GUEST_MAX_CHARS,
            hourly_limit=GUEST_HOURLY_LIMIT,
            remaining_quota=remaining,
            priority=1,
            has_key=False,
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


def resolve_output_dir(auth_ctx: AuthContext, session_id: Optional[str] = None) -> Path:
    """Resolve the scoped output root directory for a user based on tier and session.
    
    Structure:
    - Key Users  : outputs/keys/<storage_slug>/   (Permanent)
    - Guest Users: outputs/ephemeral/<session_id>/ (Short-lived, 30m TTL)
    """
    base_outputs = Path(os.environ.get("ZEROTTS_OUTPUT_DIR", _ROOT / "outputs"))

    if auth_ctx.has_key and auth_ctx.storage_slug:
        target = base_outputs / "keys" / auth_ctx.storage_slug
    else:
        # Ephemeral Guest session
        clean_sid = re.sub(r"[^a-zA-Z0-9_\-]", "", (session_id or "").strip())
        if not clean_sid or len(clean_sid) < 4:
            clean_sid = f"guest_{secrets.token_hex(6)}"
        target = base_outputs / "ephemeral" / clean_sid

    target.mkdir(parents=True, exist_ok=True)
    return target


class StorageCleaner:
    """Cleans expired ephemeral (guest) sessions and removes storage of invalid/deleted keys."""

    EPHEMERAL_TTL_SEC = 30 * 60  # 30 minutes
    GUEST_MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per session

    def __init__(self, base_outputs: Optional[Path] = None):
        self.base_outputs = base_outputs or Path(os.environ.get("ZEROTTS_OUTPUT_DIR", _ROOT / "outputs"))

    def cleanup(self, purge_orphaned_keys: bool = True) -> Dict[str, Any]:
        """Perform comprehensive cleanup of expired ephemeral sessions and invalid keys."""
        now = time.time()
        stats = {
            "deleted_ephemeral_dirs": 0,
            "deleted_invalid_key_dirs": 0,
            "freed_bytes": 0,
        }

        # 1. Clean Ephemeral Guest Folders (> 30 mins or > 50MB)
        ephemeral_root = self.base_outputs / "ephemeral"
        if ephemeral_root.is_dir():
            for item in list(ephemeral_root.iterdir()):
                if item.is_dir():
                    try:
                        mtime = item.stat().st_mtime
                        is_expired = (now - mtime) > self.EPHEMERAL_TTL_SEC

                        files = list(item.rglob("*"))
                        size = sum(f.stat().st_size for f in files if f.is_file())

                        if is_expired:
                            shutil.rmtree(item, ignore_errors=True)
                            stats["deleted_ephemeral_dirs"] += 1
                            stats["freed_bytes"] += size
                        elif size > self.GUEST_MAX_SIZE_BYTES:
                            wav_files = sorted(
                                [f for f in files if f.is_file() and f.suffix == ".wav"],
                                key=lambda f: f.stat().st_mtime,
                            )
                            while wav_files and size > (self.GUEST_MAX_SIZE_BYTES * 0.7):
                                oldest = wav_files.pop(0)
                                f_sz = oldest.stat().st_size
                                oldest.unlink(missing_ok=True)
                                sidecar = oldest.with_suffix(oldest.suffix + ".json")
                                if sidecar.exists():
                                    sidecar.unlink(missing_ok=True)
                                size -= f_sz
                                stats["freed_bytes"] += f_sz
                    except Exception as e:
                        print(f"[Cleanup] ⚠️ Error checking ephemeral dir {item}: {e}")

        # 2. Clean Invalid / Deleted Key Folders
        if purge_orphaned_keys:
            keys_root = self.base_outputs / "keys"
            if keys_root.is_dir():
                auth_manager.load_keys()
                # Active valid slugs
                valid_slugs: Set[str] = {
                    rec.storage_slug for rec in auth_manager.keys.values() if rec.is_active and rec.storage_slug
                }
                for item in list(keys_root.iterdir()):
                    if item.is_dir() and item.name not in valid_slugs:
                        try:
                            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                            shutil.rmtree(item, ignore_errors=True)
                            stats["deleted_invalid_key_dirs"] += 1
                            stats["freed_bytes"] += size
                        except Exception as e:
                            print(f"[Cleanup] ⚠️ Error cleaning orphaned key dir {item}: {e}")

        if stats["deleted_ephemeral_dirs"] > 0 or stats["deleted_invalid_key_dirs"] > 0:
            freed_mb = stats["freed_bytes"] / (1024 * 1024)
            print(f"[Cleanup] 🧹 Đã giải phóng {freed_mb:.2f} MB ({stats['deleted_ephemeral_dirs']} phiên khách, {stats['deleted_invalid_key_dirs']} thư mục key không hợp lệ).")

        return stats

    def cleanup_expired(self) -> Dict[str, Any]:
        """Alias for background loop compatibility."""
        return self.cleanup(purge_orphaned_keys=True)
