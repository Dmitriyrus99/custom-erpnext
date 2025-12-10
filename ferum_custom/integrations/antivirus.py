from __future__ import annotations

"""Antivirus integration for uploaded files (ClamAV support).

Usage:
    ok, signature = scan_bytes(content, filename)
    if not ok: block upload

Configuration (Ferum Custom Settings or site_config):
    enable_antivirus = true/false (default: false)
    antivirus_engine = 'clamav' (default)
    clamd_socket = '/var/run/clamav/clamd.ctl' (optional)
    clamscan_path = 'clamscan' (fallback when clamd is unavailable)
"""

import os
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import frappe

from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled


def _clamd_scan(path: str) -> Tuple[bool, str | None]:
    """Scan a file via clamd socket (preferred)."""
    sock_path = (get_setting("clamd_socket") or "/var/run/clamav/clamd.ctl").strip()
    if not os.path.exists(sock_path):
        return False, "clamd socket not found"
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect(sock_path)
            s.sendall(b"zINSTREAM\n")
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    s.sendall(len(chunk).to_bytes(4, byteorder="big") + chunk)
            s.sendall((0).to_bytes(4, byteorder="big"))
            resp = s.recv(4096).decode("utf-8", errors="ignore")
        # Response example: stream: OK or stream: Eicar-Test-Signature FOUND
        if "FOUND" in resp:
            sig = resp.split(":", 1)[-1].replace("FOUND", "").strip()
            return False, sig
        return True, None
    except Exception as exc:
        frappe.log_error(frappe.get_traceback(), f"clamd scan failed: {exc}")
        return False, "clamd error"


def _clamscan_cmd(path: str) -> Tuple[bool, str | None]:
    """Scan a file via clamscan subprocess."""
    exe = (get_setting("clamscan_path") or "clamscan").strip()
    try:
        proc = subprocess.run([exe, "--no-summary", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        out = proc.stdout.decode("utf-8", errors="ignore")
        # Output: /path/file: OK or /path/file: Eicar-Test-Signature FOUND
        if "FOUND" in out:
            sig = out.split(":", 1)[-1].replace("FOUND", "").strip()
            return False, sig
        return True, None
    except FileNotFoundError:
        return False, "clamscan not installed"
    except Exception as exc:
        frappe.log_error(frappe.get_traceback(), f"clamscan failed: {exc}")
        return False, "clamscan error"


def scan_bytes(content: bytes, filename: str | None = None) -> Tuple[bool, str | None]:
    """Scan bytes using configured antivirus; returns (ok, signature)."""
    if not is_feature_enabled("enable_antivirus"):
        return True, None
    engine = (get_setting("antivirus_engine") or "clamav").strip().lower()
    # Write to temp file and scan
    with tempfile.NamedTemporaryFile(prefix="upload_", suffix=Path(filename or "upload.bin").suffix, delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        if engine == "clamav":
            ok, sig = _clamd_scan(tmp.name)
            if not ok and (sig == "clamd socket not found" or sig == "clamd error"):
                ok, sig = _clamscan_cmd(tmp.name)
            return ok, sig
    return True, None

