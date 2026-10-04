#!/usr/bin/env python3
"""CLI & Interactive TUI for ZeroTTS Key Management (CRUD via SSH / Bash).

Usage:
  Interactive Menu:
    python webui/manage_keys.py

  Direct CLI Subcommands:
    python webui/manage_keys.py list
    python webui/manage_keys.py create --name "Alice" [--key "custom_token"] [--max-chars 100000]
    python webui/manage_keys.py enable <KEY_OR_NAME>
    python webui/manage_keys.py disable <KEY_OR_NAME>
    python webui/manage_keys.py delete <KEY_OR_NAME> [--purge]
    python webui/manage_keys.py clean
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
_HERE = Path(__file__).parent.resolve()
_ROOT = _HERE.parent.resolve()
for _p in [str(_ROOT), str(_HERE), str(_ROOT / "src")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auth  # noqa: E402

# ANSI Color Codes for terminal
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"
DIM = "\033[2m"


def get_folder_size_mb(path: Path) -> float:
    """Calculate directory size in megabytes."""
    if not path.is_dir():
        return 0.0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def cmd_list(args: argparse.Namespace) -> None:
    """Print all registered keys in a formatted table."""
    auth.auth_manager.load_keys()
    keys = auth.auth_manager.list_keys()
    base_outputs = Path(os.environ.get("ZEROTTS_OUTPUT_DIR", _ROOT / "outputs"))

    print("\n" + "=" * 95)
    print(f"{BOLD}{CYAN}             DANH SÁCH KEY HỆ THỐNG ZEROTTS (VĨNH VIỄN & KHÔNG GIAN RIÊNG){RESET}")
    print("=" * 95)

    if not keys:
        print(f"{YELLOW}  Chưa có key nào được tạo. Hãy dùng lệnh 'create' để tạo key đầu tiên.{RESET}\n")
        return

    header = f"{'#':<3} | {'TÊN ĐỊNH DANH':<18} | {'TRẠNG THÁI':<12} | {'STORAGE (DIR / DUNG LƯỢNG)':<30} | {'SỐ KÝ TỰ':<10} | {'ĐÃ DÙNG'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 95)

    for idx, rec in enumerate(keys, 1):
        status = f"{GREEN}● Hoạt động{RESET}" if rec.is_active else f"{RED}○ Đã khóa{RESET}"
        storage_dir = base_outputs / "keys" / rec.storage_slug
        size_mb = get_folder_size_mb(storage_dir)
        storage_str = f"keys/{rec.storage_slug} ({size_mb:.1f} MB)"

        print(f"{idx:<3} | {rec.name:<18} | {status:<21} | {storage_str:<30} | {rec.max_chars:<10,} | {rec.total_used:,} lần")
        print(f"    {DIM}🔑 Token:{RESET} {BOLD}{YELLOW}{rec.key}{RESET}  {DIM}| Tạo lúc: {rec.created_at}{RESET}")
        print("-" * 95)

    print()


def cmd_create(args: argparse.Namespace) -> None:
    """Create a new permanent key."""
    name = args.name.strip() if args.name else ""
    if not name:
        name = input(f"{BOLD}Nhập tên định danh người dùng (VD: Studio_1, Nguyen_Van_A): {RESET}").strip()
    if not name:
        print(f"{RED}❌ Tên không được để trống.{RESET}")
        return

    custom_key = args.key.strip() if args.key else None
    max_chars = int(args.max_chars) if args.max_chars else 100000
    hourly_limit = int(args.hourly_limit) if args.hourly_limit else 999999

    record = auth.auth_manager.create_key(
        name=name,
        custom_key=custom_key,
        max_chars=max_chars,
        hourly_limit=hourly_limit,
    )

    print(f"\n{GREEN}✅ ĐÃ TẠO KEY THÀNH CÔNG!{RESET}")
    print(f"  • Tên định danh : {BOLD}{record.name}{RESET}")
    print(f"  • Mã Token (Key): {BOLD}{YELLOW}{record.key}{RESET}")
    print(f"  • Thư mục riêng : {BOLD}outputs/keys/{record.storage_slug}/{RESET}")
    print(f"  • Giới hạn      : {record.max_chars:,} ký tự/lần (Không giới hạn giờ)")
    print(f"  • Chính sách    : {CYAN}Lưu trữ vĩnh viễn (Miễn nhiễm dọn dẹp){RESET}\n")


def cmd_enable(args: argparse.Namespace) -> None:
    """Enable a key."""
    target = args.key_or_name
    rec = auth.auth_manager.set_key_status(target, is_active=True)
    if rec:
        print(f"{GREEN}✅ Đã kích hoạt key: '{rec.name}' ({rec.key}){RESET}")
    else:
        print(f"{RED}❌ Không tìm thấy key hoặc tên: '{target}'{RESET}")


def cmd_disable(args: argparse.Namespace) -> None:
    """Disable a key."""
    target = args.key_or_name
    rec = auth.auth_manager.set_key_status(target, is_active=False)
    if rec:
        print(f"{YELLOW}⏸️ Đã tạm khóa key: '{rec.name}' ({rec.key}){RESET}")
    else:
        print(f"{RED}❌ Không tìm thấy key hoặc tên: '{target}'{RESET}")


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete a key."""
    target = args.key_or_name
    purge = getattr(args, "purge", False)
    rec = auth.auth_manager.delete_key(target, purge_storage=purge)
    if rec:
        purge_msg = " và đã xóa toàn bộ thư mục lưu trữ!" if purge else " (Thư mục dữ liệu được giữ lại)."
        print(f"{GREEN}🗑️ Đã xóa vĩnh viễn key '{rec.name}' ({rec.key}){purge_msg}{RESET}")
    else:
        print(f"{RED}❌ Không tìm thấy key hoặc tên: '{target}'{RESET}")


def cmd_clean(args: argparse.Namespace) -> None:
    """Run manual storage cleanup for expired guest sessions and invalid keys."""
    print(f"{CYAN}🧹 Đang quét dọn dẹp các phiên ngắn hết hạn và thư mục key không còn hợp lệ...{RESET}")
    cleaner = auth.StorageCleaner()
    stats = cleaner.cleanup(purge_orphaned_keys=True)
    freed_mb = stats["freed_bytes"] / (1024 * 1024)
    print(f"{GREEN}✅ Hoàn tất dọn dẹp:{RESET}")
    print(f"  • Đã xóa phiên khách hết hạn : {stats['deleted_ephemeral_dirs']}")
    print(f"  • Đã xóa thư mục key vô lệ  : {stats['deleted_invalid_key_dirs']}")
    print(f"  • Dung lượng đã giải phóng   : {BOLD}{freed_mb:.2f} MB{RESET}\n")


def interactive_menu() -> None:
    """Render interactive CLI terminal menu for easy SSH administration."""
    while True:
        print("\n" + "=" * 60)
        print(f"{BOLD}{CYAN}       QUẢN LÝ KEY & STORAGE ZEROTTS (SSH CLI){RESET}")
        print("=" * 60)
        print("  [1] 📋 Xem danh sách Key & Dung lượng")
        print("  [2] ➕ Tạo Key mới (Vĩnh viễn)")
        print("  [3] 🔄 Bật / Tắt Key (Enable/Disable)")
        print("  [4] 🗑️ Xóa Key (Delete Key)")
        print("  [5] 🧹 Dọn dẹp Storage rác ngay (Run Cleanup)")
        print("  [0] 🚪 Thoát")
        print("=" * 60)

        choice = input(f"{BOLD}Chọn chức năng (0-5): {RESET}").strip()

        if choice == "1":
            cmd_list(argparse.Namespace())
        elif choice == "2":
            cmd_create(argparse.Namespace(name=None, key=None, max_chars=100000, hourly_limit=999999))
        elif choice == "3":
            auth.auth_manager.load_keys()
            target = input(f"{BOLD}Nhập Tên hoặc Token của Key cần đổi trạng thái: {RESET}").strip()
            if target:
                rec = auth.auth_manager.find_key(target)
                if not rec:
                    print(f"{RED}❌ Không tìm thấy key!{RESET}")
                else:
                    new_status = not rec.is_active
                    auth.auth_manager.set_key_status(rec.key, new_status)
                    state_str = f"{GREEN}Hoạt động{RESET}" if new_status else f"{RED}Khóa{RESET}"
                    print(f"👉 Đã chuyển trạng thái key '{rec.name}' sang: {state_str}")
        elif choice == "4":
            auth.auth_manager.load_keys()
            target = input(f"{BOLD}Nhập Tên hoặc Token của Key cần XÓA: {RESET}").strip()
            if target:
                rec = auth.auth_manager.find_key(target)
                if not rec:
                    print(f"{RED}❌ Không tìm thấy key!{RESET}")
                else:
                    confirm = input(f"{RED}⚠️ Bạn có chắc chắn muốn xóa key '{rec.name}' ({rec.key})? (y/N): {RESET}").strip().lower()
                    if confirm == "y":
                        purge_in = input(f"Xóa luôn thư mục lưu trữ outputs/keys/{rec.storage_slug}/? (y/N): ").strip().lower()
                        auth.auth_manager.delete_key(rec.key, purge_storage=(purge_in == "y"))
                        print(f"{GREEN}✅ Đã xóa key thành công!{RESET}")
        elif choice == "5":
            cmd_clean(argparse.Namespace())
        elif choice == "0" or choice.lower() in ("q", "exit"):
            print(f"{CYAN}Tạm biệt!{RESET}\n")
            break
        else:
            print(f"{YELLOW}Lựa chọn không hợp lệ, vui lòng chọn lại.{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ZeroTTS Key & Storage Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list
    p_list = subparsers.add_parser("list", help="List all keys")

    # create
    p_create = subparsers.add_parser("create", help="Create a new permanent key")
    p_create.add_argument("--name", "-n", type=str, help="User/Organization Name")
    p_create.add_argument("--key", "-k", type=str, default=None, help="Custom token")
    p_create.add_argument("--max-chars", type=int, default=100000, help="Max chars limit per generation")
    p_create.add_argument("--hourly-limit", type=int, default=999999, help="Hourly requests limit")

    # enable
    p_enable = subparsers.add_parser("enable", help="Enable a key")
    p_enable.add_argument("key_or_name", type=str, help="Key token or Name to enable")

    # disable
    p_disable = subparsers.add_parser("disable", help="Disable a key")
    p_disable.add_argument("key_or_name", type=str, help="Key token or Name to disable")

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a key")
    p_delete.add_argument("key_or_name", type=str, help="Key token or Name to delete")
    p_delete.add_argument("--purge", "-p", action="store_true", help="Also delete dedicated storage folder")

    # clean
    p_clean = subparsers.add_parser("clean", help="Run storage cleanup for expired guest sessions & invalid keys")

    args = parser.parse_args()

    if not args.command:
        interactive_menu()
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "enable":
        cmd_enable(args)
    elif args.command == "disable":
        cmd_disable(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "clean":
        cmd_clean(args)


if __name__ == "__main__":
    main()
