#!/usr/bin/env python3
"""ZeroTTS Token & Access Control CLI (for SSH Bash Management).

Usage:
    python auth_cli.py master                      # Show or create owner Master Key
    python auth_cli.py list                        # List all keys and usage statistics
    python auth_cli.py create --name "Tên" [options] # Create new key
    python auth_cli.py revoke <key>                # Deactivate a key
    python auth_cli.py delete <key>                # Permanently remove a key
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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

# Ensure webui module is in sys.path
_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "webui"))

from webui.auth import auth_manager


def cmd_master(_args):
    """Show or create master key."""
    keys = [k for k in auth_manager.list_keys() if k.tier == "master" and k.is_active]
    if keys:
        print("\n🔑 MASTER KEY HIỆN TẠI (Dành cho Chính chủ):")
        for k in keys:
            print(f"  • Token:     {k.key}")
            print(f"    Tên:       {k.name}")
            print(f"    Tạo ngày:  {k.created_at}")
            print(f"    Đã dùng:   {k.total_used} lần")
            print(f"    Trạng thái: {'Đang hoạt động ✅' if k.is_active else 'Đã vô hiệu hóa ❌'}")
            print("-" * 50)
    else:
        rec = auth_manager.create_key(name="Admin Master", tier="master")
        print("\n✨ Đã tạo Master Key mới:")
        print(f"  Token: {rec.key}")
    print("\n👉 Hãy sao chép Token này và dán vào ô '🔑 Nhập VIP / Access Key' trên WebUI!\n")


def cmd_list(_args):
    """List all API keys in a clean table."""
    keys = auth_manager.list_keys()
    if not keys:
        print("\n(Chưa có key nào trong hệ thống)\n")
        return

    print("\n" + "=" * 80)
    print(f"{'STT':<4} {'TIER':<8} {'TÊN / MÔ TẢ':<22} {'KÝ TỰ':<8} {'HẠN DÙNG':<14} {'ĐÃ DÙNG':<8} {'TOKEN':<20}")
    print("-" * 80)
    for idx, k in enumerate(keys, 1):
        status_icon = "✅" if k.is_active else "❌"
        exp = k.expires_at[:10] if k.expires_at else "Vĩnh viễn"
        chars = f"{k.max_chars:,}" if k.tier != "master" else "Vô hạn"
        print(f"{idx:<4} {k.tier.upper():<8} {k.name[:20]:<22} {chars:<8} {exp:<14} {k.total_used:<8} {k.key} {status_icon}")
    print("=" * 80 + "\n")


def cmd_create(args):
    """Create a new key."""
    rec = auth_manager.create_key(
        name=args.name,
        tier=args.tier,
        max_chars=args.chars,
        hourly_limit=args.limit,
        days_valid=args.days,
        custom_key=args.key,
    )
    print("\n🎉 TẠO TOKEN THÀNH CÔNG!")
    print(f"  • Token:        {rec.key}")
    print(f"  • Tên:          {rec.name}")
    print(f"  • Tier:         {rec.tier.upper()}")
    print(f"  • Giới hạn:     {rec.max_chars:,} ký tự / {rec.hourly_limit} lượt/giờ")
    print(f"  • Hạn dùng:     {rec.expires_at or 'Vĩnh viễn'}")
    print(f"  • Lưu trữ tại:  {auth_manager.auth_file}\n")


def cmd_revoke(args):
    """Revoke/deactivate a key."""
    success = auth_manager.revoke_key(args.token)
    if success:
        print(f"\n🔒 Đã vô hiệu hóa token: {args.token}\n")
    else:
        print(f"\n⚠️ Không tìm thấy token: {args.token}\n")


def cmd_delete(args):
    """Delete a key."""
    success = auth_manager.delete_key(args.token)
    if success:
        print(f"\n🗑️ Đã xóa vĩnh viễn token: {args.token}\n")
    else:
        print(f"\n⚠️ Không tìm thấy token: {args.token}\n")


def main():
    parser = argparse.ArgumentParser(description="ZeroTTS Auth & Token Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # master
    p_master = subparsers.add_parser("master", help="Xem hoặc tạo Master Key của chính chủ")
    p_master.set_defaults(func=cmd_master)

    # list
    p_list = subparsers.add_parser("list", help="Liệt kê toàn bộ Token & thống kê sử dụng")
    p_list.set_defaults(func=cmd_list)

    # create
    p_create = subparsers.add_parser("create", help="Tạo Token mới cho VIP hoặc Bạn bè")
    p_create.add_argument("--name", required=True, help="Tên hoặc người nhận Token (VD: 'Bạn Nam', 'Recruiter')")
    p_create.add_argument("--tier", default="vip", choices=["vip", "master"], help="Cấp bậc (vip / master)")
    p_create.add_argument("--chars", type=int, default=2000, help="Số ký tự tối đa cho mỗi lần tạo (mặc định: 2000)")
    p_create.add_argument("--limit", type=int, default=50, help="Số lần tạo tối đa mỗi giờ (mặc định: 50)")
    p_create.add_argument("--days", type=int, default=None, help="Số ngày hiệu lực (bỏ trống = vĩnh viễn)")
    p_create.add_argument("--key", default=None, help="Tự đặt token key tùy chọn")
    p_create.set_defaults(func=cmd_create)

    # revoke
    p_revoke = subparsers.add_parser("revoke", help="Vô hiệu hóa một Token")
    p_revoke.add_argument("token", help="Token cần vô hiệu hóa")
    p_revoke.set_defaults(func=cmd_revoke)

    # delete
    p_del = subparsers.add_parser("delete", help="Xóa vĩnh viễn một Token")
    p_del.add_argument("token", help="Token cần xóa")
    p_del.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
