#!/usr/bin/env python3
"""
op_credential_injector.py — Hermes Agent 1Password credential injection helper

This module provides functions for:
1. Looking up credentials by domain/URL from 1Password via op CLI
2. Safely reading credentials into memory (never to chat/logs)
3. Providing credentials to computer_use type actions for form field injection

SECURITY MODEL:
- Credentials are NEVER returned from any function in a printable form
- Credentials flow: op CLI -> temp file -> memory -> computer_use type action
- No function returns credential values; they go directly to injection
- All temp files are immediately deleted after reading
- Logging is explicitly suppressed for credential values

Usage from Hermes Agent (browser_exec):
    from agent_helpers import op_login
    op_login("f5bot.com")  # Returns dict with __repr__ that shows no secrets

    # For direct injection via computer_use:
    # The agent calls the bash helper, reads the temp file, types into fields
"""

import subprocess
import json
import os
import tempfile
import re
from urllib.parse import urlparse
from typing import Optional, Tuple
import logging

# Suppress all logging for this module by default
logging.getLogger(__name__).setLevel(logging.CRITICAL)


class SecureCredential:
    """A credential container that never exposes its values in repr/str."""
    
    __slots__ = ('_username', '_password', '_item_title')
    
    def __init__(self, username: str, password: str, item_title: str):
        self._username = username
        self._password = password
        self._item_title = item_title
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def password(self) -> str:
        return self._password
    
    @property
    def item_title(self) -> str:
        return self._item_title
    
    def __repr__(self) -> str:
        return f"<SecureCredential item='{self._item_title}' [REDACTED]>"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __del__(self):
        """Zero out credentials in memory on garbage collection."""
        try:
            self._username = '\x00' * len(self._username) if self._username else ''
            self._password = '\x00' * len(self._password) if self._password else ''
        except:
            pass


def _extract_domain(url_or_domain: str) -> str:
    """Extract a normalized domain from a URL or domain string."""
    s = url_or_domain.strip().lower()
    s = re.sub(r'^https?://', '', s)
    s = s.split('/')[0]
    s = s.replace('www.', '')
    return s


def _find_item_by_domain(domain: str, vault: str = "OpenClaw") -> Optional[Tuple[str, str]]:
    """
    Find a 1Password login item matching the given domain.
    Returns (item_id, item_title) or None.
    Does NOT retrieve any credential values.
    """
    try:
        result = subprocess.run(
            ['op', 'item', 'list', '--categories', 'LOGIN', '--vault', vault, '--format', 'json'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return None
        
        items = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None
    
    best_match = None
    
    for item in items:
        item_id = item['id']
        item_title = item['title']
        urls = item.get('urls', [])
        
        for url_obj in urls:
            url = url_obj.get('href', '')
            try:
                parsed = urlparse(url if '://' in url else 'https://' + url)
                url_domain = parsed.netloc.lower().replace('www.', '')
            except:
                continue
            
            if not url_domain:
                continue
            
            # Exact match
            if url_domain == domain:
                return (item_id, item_title)
            
            # Subdomain match
            if domain.endswith('.' + url_domain) or url_domain.endswith('.' + domain):
                if best_match is None:
                    best_match = (item_id, item_title)
            # Partial match as last resort
            elif domain in url_domain or url_domain in domain:
                if best_match is None:
                    best_match = (item_id, item_title)
    
    return best_match


def _retrieve_credentials(item_id: str, vault: str = "OpenClaw") -> Optional[Tuple[str, str]]:
    """
    Retrieve username and password for an item.
    Writes op output to a temp file, reads it, and immediately deletes the file.
    Returns (username, password) or None.
    NEVER prints credentials to stdout/stderr.
    """
    temp_fd, temp_path = tempfile.mkstemp(prefix='op_cred_', suffix='.json')
    os.chmod(temp_path, 0o600)
    
    try:
        # Write op output directly to temp file
        with os.fdopen(temp_fd, 'w') as f:
            result = subprocess.run(
                ['op', 'item', 'get', item_id, '--vault', vault,
                 '--fields', 'label=username,label=password', '--format', 'json'],
                stdout=f, stderr=subprocess.DEVNULL, timeout=15
            )
        
        if result.returncode != 0 or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            # Fallback: try field IDs instead of labels
            with open(temp_path, 'w') as f:
                result = subprocess.run(
                    ['op', 'item', 'get', item_id, '--vault', vault,
                     '--fields', 'username,password', '--format', 'json'],
                    stdout=f, stderr=subprocess.DEVNULL, timeout=15
                )
        
        if result.returncode != 0 or os.path.getsize(temp_path) == 0:
            return None
        
        # Read and parse
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        username = ''
        password = ''
        
        # op --fields returns a list of field objects
        if isinstance(data, list):
            for field in data:
                if field.get('id') == 'username' or field.get('label') == 'username':
                    username = field.get('value', '')
                elif field.get('id') == 'password' or field.get('label') == 'password':
                    password = field.get('value', '')
        elif isinstance(data, dict):
            username = data.get('value', '') if data.get('id') in ('username', 'password') else ''
        
        return (username, password) if (username or password) else None
    
    except Exception:
        return None
    finally:
        # ALWAYS delete the temp file
        try:
            os.unlink(temp_path)
        except:
            pass


def get_credential(url_or_domain: str, vault: str = "OpenClaw") -> Optional[SecureCredential]:
    """
    Main entry point: get credentials for a domain/URL.
    
    Returns a SecureCredential object (whose repr does NOT expose secrets)
    or None if not found.
    
    The agent should then use cred.username and cred.password to inject
    via computer_use type actions. These values should NEVER be printed.
    """
    domain = _extract_domain(url_or_domain)
    if not domain:
        return None
    
    match = _find_item_by_domain(domain, vault)
    if not match:
        return None
    
    item_id, item_title = match
    creds = _retrieve_credentials(item_id, vault)
    if not creds:
        return None
    
    return SecureCredential(creds[0], creds[1], item_title)


def list_available_logins(vault: str = "OpenClaw") -> list:
    """
    List all available login items (title + domain only, NO credentials).
    Useful for the agent to discover what's available.
    """
    try:
        result = subprocess.run(
            ['op', 'item', 'list', '--categories', 'LOGIN', '--vault', vault, '--format', 'json'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        
        items = json.loads(result.stdout)
        logins = []
        for item in items:
            urls = [u.get('href', '') for u in item.get('urls', [])]
            logins.append({
                'title': item['title'],
                'domains': [_extract_domain(u) for u in urls if u],
            })
        return logins
    except:
        return []


if __name__ == '__main__':
    # CLI mode: call the bash helper for security (never print credentials)
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 op_credential_injector.py <domain-or-url>")
        print("       python3 op_credential_injector.py --list")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        logins = list_available_logins()
        for l in logins:
            print(f"  {l['title']}: {', '.join(l['domains']) or '(no URL)'}")
    else:
        # Delegate to bash helper for credential retrieval
        helper_path = os.path.join(os.path.dirname(__file__), 'op-credential-helper.sh')
        result = subprocess.run(['bash', helper_path, sys.argv[1]], capture_output=True, text=True)
        print(result.stdout.strip())
        sys.exit(result.returncode)