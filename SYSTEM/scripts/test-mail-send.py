#!/usr/bin/env python3
"""Test email send via mail_client.py — diagnostic for mail issues."""
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
from mail_client import send_email

try:
    result = send_email(
        from_email='kenneth@agentictrust.app',
        to_email='kenneth@agentictrust.app',
        subject='TEST — Kit mail diagnostic',
        body='Test email from Kit diagnostic. If you see this, outbound mail is working.',
        signature=False
    )
    print(f'SEND RESULT: {result}')
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'SEND FAIL: {e}')