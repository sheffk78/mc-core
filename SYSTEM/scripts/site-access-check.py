#!/usr/bin/env python3
"""
site-access-check.py — Verify browser access to regularly-used web apps.

For each site in the registry:
  1. Opens it in agent Chrome (via CDP)
  2. Checks if we're logged in
  3. If not, retrieves credentials from 1Password and logs in via CDP
  4. Verifies post-login state
  5. Reports success/failure

Usage:
  python3 site-access-check.py                    # Check all sites
  python3 site-access-check.py coverr.co          # Check specific site
  python3 site-access-check.py --list             # List configured sites
  python3 site-access-check.py --close-all        # Close all agent Chrome tabs after

The site registry is defined in SITE_REGISTRY below.
Credentials are retrieved via op-credential-helper.sh — NEVER printed to stdout.
"""

import json
import os
import subprocess
import sys
import time
import websocket

CDP_URL = "http://localhost:9222"
OP_HELPER = os.path.expanduser("~/.openclaw/workspace/SYSTEM/scripts/op-credential-helper.sh")
ENSURE_SCRIPT = os.path.expanduser("~/.openclaw/workspace/SYSTEM/scripts/ensure-chrome-awake.sh")

# ─── Site Registry ──────────────────────────────────────────────────────────
# Each entry: domain, url (the page we want to reach), login_url (if different),
# login_check (JS expression that returns true if logged in),
# email_selector, password_selector, submit_selector (for auto-login)
SITE_REGISTRY = [
    {
        "domain": "coverr.co",
        "url": "https://coverr.co/studio/ai-images-generator",
        "login_check": "!document.querySelector('input[type=password]') && document.body.innerText.includes('Credits')",
        "email_selector": "#email",
        "password_selector": "#password",
        "submit_selector": "button",
        "submit_text": "sign in",
        "notes": "AI image/video generator — TJB uses for birth illustrations"
    },
    {
        "domain": "app.mailercloud.com",
        "url": "https://app.mailercloud.com/",
        "login_check": "!document.querySelector('input[name=password]') && !window.location.href.includes('login')",
        "email_selector": "input[name='email'], input[type='email'], input[type='text'][name='email']",
        "password_selector": "input[type='password'], input[name='password']",
        "submit_selector": "button[type='submit']",
        "submit_text": "log in",
        "requires_visual_login": True,
        "notes": "Email platform — BootstrapVue form ignores CDP value setting, needs computer_use typing"
    },
    {
        "domain": "admin.mistral.ai",
        "url": "https://admin.mistral.ai/",
        "login_check": "!document.querySelector('input[type=password]')",
        "email_selector": "input[type='email'], input[name*='email']",
        "password_selector": "input[type='password']",
        "submit_selector": "button[type='submit'], button",
        "submit_text": "login",
        "notes": "Mistral AI API console"
    },
    {
        "domain": "app.outscraper.cloud",
        "url": "https://app.outscraper.cloud/",
        "login_check": "!document.querySelector('input[type=password]') && !window.location.href.includes('login')",
        "email_selector": "#login_email, input[type='email'], input[type='text'][placeholder*='email']",
        "password_selector": "#login_password, input[type='password']",
        "submit_selector": "button[type='submit']",
        "submit_text": "log in",
        "notes": "Scraping platform — Ant Design form ignores CDP value setting, needs computer_use typing"
    },
    {
        "domain": "zerobounce.net",
        "url": "https://www.zerobounce.net/login/",
        "login_check": "!document.querySelector('input[type=password]')",
        "email_selector": "input[type='email'], input[name*='email'], input[name*='username']",
        "password_selector": "input[type='password']",
        "submit_selector": "button[type='submit'], button",
        "submit_text": "login",
        "notes": "Email validation"
    },
    {
        "domain": "postmarkapp.com",
        "url": "https://account.postmarkapp.com/",
        "login_check": "!document.querySelector('input[type=password]')",
        "email_selector": "input[type='email'], input[name*='email']",
        "password_selector": "input[type='password']",
        "submit_selector": "button[type='submit'], button",
        "submit_text": "log in",
        "notes": "Postmark email delivery"
    },
    {
        "domain": "aeriusview.com",
        "url": "https://aeriusview.com/",
        "login_check": "!document.querySelector('input[type=password]')",
        "email_selector": "input[type='email'], input[name*='email']",
        "password_selector": "input[type='password']",
        "submit_selector": "button[type='submit'], button",
        "submit_text": "login",
        "notes": "AeriusView dashboard"
    },
    {
        "domain": "dash.bunny.net",
        "url": "https://dash.bunny.net/",
        "login_check": "!document.querySelector('input[type=password]') && !window.location.href.includes('login')",
        "email_selector": "#username, input[type='email'], input[type='text'][placeholder*='Email']",
        "password_selector": "#password, input[type='password']",
        "submit_selector": "button[type='submit']",
        "submit_text": "log in",
        "notes": "Bunny.net CDN — Vue.js form ignores CDP value setting, needs computer_use typing"
    },
]


def ensure_chrome():
    """Ensure agent Chrome is running with CDP."""
    if os.path.exists(ENSURE_SCRIPT):
        subprocess.run(["bash", ENSURE_SCRIPT, "120"], capture_output=True, timeout=15)
    
    # Verify CDP
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "3", f"{CDP_URL}/json/version"],
            capture_output=True, text=True, timeout=5
        )
        data = json.loads(result.stdout)
        return True, data.get("Browser", "?")
    except:
        return False, None


def cdp_open_tab(url):
    """Open a new tab via CDP. Returns (tab_id, ws_url)."""
    result = subprocess.run(
        ["curl", "-s", "-X", "PUT", f"{CDP_URL}/json/new?{url}"],
        capture_output=True, text=True, timeout=10
    )
    data = json.loads(result.stdout)
    return data.get("id"), data.get("webSocketDebuggerUrl", "")


def cdp_close_tab(tab_id):
    """Close a tab via CDP."""
    subprocess.run(
        ["curl", "-s", "-X", "DELETE", f"{CDP_URL}/json/close/{tab_id}"],
        capture_output=True, timeout=5
    )


def cdp_eval(ws_url, js_expression, timeout=10):
    """Evaluate JavaScript on a page via CDP WebSocket. Returns the value."""
    ws = websocket.create_connection(ws_url, timeout=timeout)
    try:
        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": js_expression, "returnByValue": True}
        }))
        result = json.loads(ws.recv())
        return result.get("result", {}).get("result", {}).get("value")
    finally:
        ws.close()


def cdp_eval_multi(ws_url, commands, timeout=15):
    """Send multiple CDP commands on one WebSocket connection. Returns list of results."""
    ws = websocket.create_connection(ws_url, timeout=timeout)
    results = []
    try:
        for i, (method, params) in enumerate(commands):
            ws.send(json.dumps({"id": i + 1, "method": method, "params": params}))
            result = json.loads(ws.recv())
            results.append(result)
            time.sleep(0.3)
    finally:
        ws.close()
    return results


def get_1password_creds(domain):
    """Retrieve credentials from 1Password. Returns (username, password) or (None, None)."""
    result = subprocess.run(
        ["bash", OP_HELPER, domain],
        capture_output=True, text=True, timeout=15
    )
    output = result.stdout.strip()
    if not output.startswith("FOUND"):
        return None, None
    
    parts = output.split(None, 2)
    temp_file = parts[1]
    
    try:
        with open(temp_file, 'r') as f:
            fields = json.load(f)
        
        username = ""
        password = ""
        for field in fields:
            label = field.get('label', '')
            field_id = field.get('id', '')
            # Match by label OR id — 1Password items have varying label formats
            if label in ('email', 'username') or field_id == 'username':
                username = field.get('value', '')
            elif label == 'password' or field_id == 'password':
                password = field.get('value', '')
        
        return username, password
    except:
        return None, None
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass


def check_site(site):
    """Check a single site. Returns dict with results."""
    domain = site["domain"]
    url = site["url"]
    
    result = {
        "domain": domain,
        "url": url,
        "status": "unknown",
        "logged_in": False,
        "auto_logged_in": False,
        "error": None,
        "tab_id": None,
    }
    
    try:
        # Open the page
        tab_id, ws_url = cdp_open_tab(url)
        result["tab_id"] = tab_id
        if not tab_id:
            result["status"] = "failed"
            result["error"] = "Could not open tab via CDP"
            return result
        
        # Wait for page to load
        time.sleep(4)
        
        # Check if already logged in (cookie-based session)
        check_js = f"""JSON.stringify({{
            url: window.location.href,
            title: document.title,
            loggedIn: (function() {{ try {{ return ({site['login_check']}); }} catch(e) {{ return false; }} }})(),
            hasLoginForm: !!document.querySelector('input[type=password]'),
            bodySnippet: document.body ? document.body.innerText.substring(0, 300) : '(no body)'
        }})"""
        
        page_state = cdp_eval(ws_url, check_js)
        if page_state:
            state = json.loads(page_state)
            result["page_url"] = state.get("url", "?")
            result["page_title"] = state.get("title", "?")
            result["logged_in"] = state.get("loggedIn", False)
            
            if result["logged_in"]:
                result["status"] = "ok"
                result["message"] = "Already logged in (session cookie active)"
                return result
        
        # Not logged in — try auto-login with 1Password
        username, password = get_1password_creds(domain)
        if not username and not password:
            result["status"] = "no_credentials"
            result["error"] = "No 1Password credentials found for this domain"
            return result
        
        # Check if login form is visible, if not try to trigger sign-in
        if not state.get("hasLoginForm"):
            # Try clicking a Sign In button
            signin_js = """(function() {
                var els = document.querySelectorAll('a, button');
                for (var i = 0; i < els.length; i++) {
                    var text = els[i].textContent.trim().toLowerCase();
                    if (text === 'sign in' || text === 'log in' || text === 'login') {
                        els[i].click();
                        return true;
                    }
                }
                return false;
            })()"""
            cdp_eval(ws_url, signin_js)
            time.sleep(3)
        
        # Inject credentials using React-compatible approach
        email_sel = site["email_selector"]
        pass_sel = site["password_selector"]
        
        inject_js = f"""(function() {{
            var emailInput = document.querySelector('{email_sel}');
            var passwordInput = document.querySelector('{pass_sel}');
            if (!emailInput || !passwordInput) {{
                return JSON.stringify({{success: false, error: 'Could not find input fields'}});
            }}
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInput, {json.dumps(username)});
            emailInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            emailInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            setter.call(passwordInput, {json.dumps(password)});
            passwordInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            passwordInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            return JSON.stringify({{success: true, emailLen: emailInput.value.length, passLen: passwordInput.value.length}});
        }})()"""
        
        inject_result = cdp_eval(ws_url, inject_js)
        if inject_result:
            ir = json.loads(inject_result)
            if not ir.get("success"):
                result["status"] = "inject_failed"
                result["error"] = ir.get("error", "Unknown injection error")
                return result
        
        # Click submit button
        submit_text = site.get("submit_text", "login")
        submit_js = f"""(function() {{
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {{
                var btn = buttons[i];
                var text = btn.textContent.trim().toLowerCase();
                var form = btn.closest('form') || btn.parentElement;
                if (form && form.querySelector('input[type=password]')) {{
                    if (text.includes('{submit_text}') || btn.type === 'submit') {{
                        btn.click();
                        return 'clicked: ' + text;
                    }}
                }}
            }}
            // Fallback: submit form directly
            var form = document.querySelector('form');
            if (form && form.querySelector('input[type=password]')) {{
                form.submit();
                return 'form submitted';
            }}
            return 'no submit found';
        }})()"""
        
        cdp_eval(ws_url, submit_js)
        time.sleep(5)
        
        # Verify login
        verify_js = f"""JSON.stringify({{
            url: window.location.href,
            title: document.title,
            loggedIn: (function() {{ try {{ return ({site['login_check']}); }} catch(e) {{ return false; }} }})(),
            hasLoginForm: !!document.querySelector('input[type=password]'),
            bodySnippet: document.body ? document.body.innerText.substring(0, 300) : '(no body)'
        }})"""
        
        verify_state = cdp_eval(ws_url, verify_js)
        if verify_state:
            vdata = json.loads(verify_state)
            result["logged_in"] = vdata.get("loggedIn", False)
            result["auto_logged_in"] = result["logged_in"]
            if result["logged_in"]:
                result["status"] = "ok"
                result["message"] = "Auto-logged in via 1Password"
            else:
                result["status"] = "login_failed"
                result["error"] = f"Login attempted but verification failed. Has login form: {vdata.get('hasLoginForm')}"
                result["body_snippet"] = vdata.get("bodySnippet", "")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


def close_all_tabs():
    """Close all tabs in agent Chrome."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "3", f"{CDP_URL}/json/list"],
            capture_output=True, text=True, timeout=5
        )
        tabs = json.loads(result.stdout)
        for tab in tabs:
            if tab.get("type") == "page":
                cdp_close_tab(tab["id"])
        return len([t for t in tabs if t.get("type") == "page"])
    except:
        return 0


def main():
    if "--list" in sys.argv:
        print("Configured sites:")
        for s in SITE_REGISTRY:
            print(f"  {s['domain']:30s}  {s['notes']}")
        return
    
    if "--close-all" in sys.argv:
        count = close_all_tabs()
        print(f"Closed {count} tab(s)")
        return
    
    # Filter to specific site if provided
    sites = SITE_REGISTRY
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        target = sys.argv[1].lower()
        sites = [s for s in SITE_REGISTRY if target in s["domain"]]
        if not sites:
            print(f"No site matching '{target}' in registry. Use --list to see options.")
            return
    
    # Ensure Chrome is ready
    print("Ensuring agent Chrome is ready...")
    ok, browser = ensure_chrome()
    if not ok:
        print("ERROR: Agent Chrome not available. Run ensure-chrome-awake.sh first.")
        return
    print(f"Chrome ready: {browser}")
    print()
    
    # Check each site
    results = []
    for site in sites:
        print(f"Checking {site['domain']}...", end=" ", flush=True)
        result = check_site(site)
        results.append(result)
        
        if result["status"] == "ok":
            if result.get("auto_logged_in"):
                print("✅ AUTO-LOGGED IN")
            else:
                print("✅ LOGGED IN (session active)")
        elif result["status"] == "no_credentials":
            print("❌ NO 1PASSWORD CREDS")
        elif result["status"] == "login_failed":
            if site.get("requires_visual_login"):
                print("⚠️  NEEDS VISUAL LOGIN (Vue/React form — use computer_use)")
            else:
                print("❌ LOGIN FAILED")
        elif result["status"] == "failed":
            print(f"❌ ERROR: {result.get('error', '?')}")
        else:
            print(f"⚠️  {result['status']}: {result.get('error', '')}")
        
        # Close the tab after checking
        if result.get("tab_id"):
            cdp_close_tab(result["tab_id"])
    
    # Summary
    print()
    print("=" * 60)
    ok_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = sum(1 for r in results if r["status"] not in ("ok",))
    print(f"Results: {ok_count} accessible, {fail_count} issues out of {len(results)} sites")
    
    if fail_count > 0:
        print("\nIssues:")
        for r in results:
            if r["status"] != "ok":
                print(f"  {r['domain']}: {r['status']} — {r.get('error', '')}")
    
    # Output JSON for programmatic use
    if "--json" in sys.argv:
        print()
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()