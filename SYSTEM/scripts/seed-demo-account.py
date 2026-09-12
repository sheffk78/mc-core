#!/usr/bin/env python3
"""
Seed a WingPoint demo account with two fully-processed trusts that mirror
the TrustOffice dashboard screenshot (Johnson Education Trust + Smith Family Trust).

Creates:
  1. A regular (non-admin) user account: demo@wingpointtrust.com
  2. Two trust tokens (used, linked to applications)
  3. Two trust applications — fully completed with EINs, documents, notarized,
     bank accounts opened, and TrustOffice integration status set to first_login.
  4. A third unused token so the dashboard shows a "1 credit remaining" state.

The trusts match the screenshot data:
  - Johnson Education Trust: California, EIN 98-7654321, created Jul 30 2026
  - Smith Family Trust:       Delaware,  EIN 12-3456789, created Jul 30 2026

Run with:
  python3 seed-demo-account.py
"""

import os
import sys
import json
import uuid
import hashlib
import hmac
import base64
import re
from datetime import datetime, timezone, timedelta

# --- Environment ---
ENCRYPTION_KEY = "wingpoint-encryption-key-32chars"
ENCRYPTION_SALT = "-XDAy2RD55LxlaeEPcHXbj3DPIP_V5Dy4bV7Y_J6uLs"
MONGO_URL = "mongodb://wingpoint:Wp2026SecUr3!@altaria.proxy.rlwy.net:24417?authSource=admin"
DB_NAME = "wingpoint"

# --- Password hashing (bcrypt via passlib-compatible) ---
# We use bcrypt directly since the app uses passlib with bcrypt rounds=12
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with 12 rounds."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

# --- SSN encryption (Fernet via PBKDF2) ---
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key():
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=ENCRYPTION_SALT.encode(),
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))

def encrypt_ssn(ssn: str) -> str:
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(ssn.encode()).decode()

# --- MongoDB ---
from pymongo import MongoClient

def main():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=15000)
    db = client[DB_NAME]

    # Check if demo account already exists
    existing = db.users.find_one({"email": "demo@wingpointtrust.com"})
    if existing:
        print(f"Demo account already exists (id={existing['id']}). Cleaning up old data...")
        # Remove old tokens and applications for this user
        db.trust_tokens.delete_many({"user_id": existing["id"]})
        db.trust_applications.delete_many({"user_id": existing["id"]})
        db.users.delete_one({"id": existing["id"]})
        print("Old demo data removed.")

    # --- Create user ---
    demo_user_id = str(uuid.uuid4())
    demo_password = "Demo2026!"
    password_hash = hash_password(demo_password)

    user_doc = {
        "_id": demo_user_id,  # Use the same id for _id and id for simplicity
        "id": demo_user_id,
        "email": "demo@wingpointtrust.com",
        "password_hash": password_hash,
        "name": "Demo User",
        "phone": "(801) 555-0199",
        "referral_source": "Demo Account",
        "role": "user",
        "priority_support": False,
        "lead_status": "won",
        "lead_owner": None,
        "email_access": False,
        "created_at": datetime(2026, 7, 28, 14, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc),
        "last_login": None,
    }

    result = db.users.insert_one(user_doc)
    print(f"Created demo user: demo@wingpointtrust.com (id={demo_user_id})")
    print(f"  Password: {demo_password}")

    # --- Timestamps ---
    # Both trusts created Jul 30, 2026 per the screenshot
    created_at = datetime(2026, 7, 30, 15, 30, 0, tzinfo=timezone.utc)
    completed_at = datetime(2026, 7, 30, 18, 45, 0, tzinfo=timezone.utc)
    updated_at = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)

    # --- Token 1: Johnson Education Trust (used) ---
    token1_id = str(uuid.uuid4())
    app1_id = str(uuid.uuid4())

    token1 = {
        "_id": token1_id,
        "id": token1_id,
        "token_code": "WPT-DEMO01",
        "user_id": demo_user_id,
        "order_id": None,
        "package_type": "single",
        "status": "used",
        "application_id": app1_id,
        "created_at": created_at,
        "used_at": completed_at,
        "granted_by_admin": "96e6b47f-948b-42ee-89d4-468be874ef5d",
    }

    # --- Token 2: Smith Family Trust (used) ---
    token2_id = str(uuid.uuid4())
    app2_id = str(uuid.uuid4())

    token2 = {
        "_id": token2_id,
        "id": token2_id,
        "token_code": "WPT-DEMO02",
        "user_id": demo_user_id,
        "order_id": None,
        "package_type": "single",
        "status": "used",
        "application_id": app2_id,
        "created_at": created_at,
        "used_at": completed_at,
        "granted_by_admin": "96e6b47f-948b-42ee-89d4-468be874ef5d",
    }

    # --- Token 3: unused credit (shows "1 credit remaining" on dashboard) ---
    token3_id = str(uuid.uuid4())
    token3 = {
        "_id": token3_id,
        "id": token3_id,
        "token_code": "WPT-DEMO03",
        "user_id": demo_user_id,
        "order_id": None,
        "package_type": "single",
        "status": "unused",
        "application_id": None,
        "created_at": created_at,
        "used_at": None,
        "granted_by_admin": "96e6b47f-948b-42ee-89d4-468be874ef5d",
    }

    db.trust_tokens.insert_many([token1, token2, token3])
    print(f"Created 3 trust tokens (2 used, 1 unused)")

    # --- SSN encryption ---
    grantor_ssn_encrypted = encrypt_ssn("529-67-2065")  # Same dummy SSN used in existing seed data
    trustee_ssn_encrypted = encrypt_ssn("529-67-2065")

    # --- Application 1: Johnson Education Trust ---
    app1 = {
        "_id": app1_id,
        "id": app1_id,
        "user_id": demo_user_id,
        "token_id": token1_id,

        # Grantor info
        "grantor_first_name": "Robert",
        "grantor_middle_name": "James",
        "grantor_last_name": "Johnson",
        "grantor_suffix": "",
        "grantor_full_name": "Robert James Johnson",
        "grantor_ssn_encrypted": grantor_ssn_encrypted,

        # Trustee info (same as grantor for demo)
        "trustee_first_name": "Robert",
        "trustee_middle_name": "James",
        "trustee_last_name": "Johnson",
        "trustee_suffix": "",
        "trustee_full_name": "Robert James Johnson",
        "trustee_name": "Robert James Johnson",
        "trustee_ssn_encrypted": trustee_ssn_encrypted,

        # WingPoint trustee
        "use_wingpoint_trustee": False,
        "trustee_service_status": "not_applicable",
        "trustee_payment_reminder_sent_at": None,

        # Role
        "role_for_trust": "trustee",

        # Customer contact
        "customer_name": "Robert Johnson",
        "customer_email": "demo@wingpointtrust.com",
        "customer_phone": "(801) 555-0199",

        # Trust details
        "trust_name": "Johnson Education Trust",
        "trust_purpose": "family",
        "trust_type": "FAMILY_TRUST",
        "trust_formation_date": "2026-07-30",
        "state_of_domicile": "CA",

        # Mailing address (California)
        "mailing_address_line1": "4500 Campus Drive",
        "mailing_address_line2": "Suite 200",
        "mailing_city": "Irvine",
        "mailing_state": "CA",
        "mailing_zip": "92612",
        "mailing_county": "Orange",

        # Entity
        "entity_type": "irrevocable_trust",

        # Workflow state — fully completed
        "status": "completed",

        # EIN + document outputs
        "ein_number": "98-7654321",
        "irs_confirmation_pdf_id": None,
        "irs_confirmation_text": "EIN confirmed via IRS EIN Assistant",
        "declaration_pdf_id": None,
        "certification_pdf_id": None,
        "certification_general_pdf_id": None,
        "certification_banking_pdf_id": None,
        "binder_kit_pdf_id": None,
        "w9_pdf_id": None,
        "ein_source": "automation",
        "ein_obtained_at": completed_at,
        "name_control": "JOHN",
        "ein_issued_date": "2026-07-30",
        "closing_month": "December",
        "confirmation_method": "digital",
        "generation_timestamp": completed_at,
        "error_log": None,

        # Notarization
        "notarized": True,
        "notarized_at": datetime(2026, 8, 5, 14, 30, 0, tzinfo=timezone.utc),
        "notarized_source": "customer",

        # Bank account
        "bank_account_opened": True,
        "bank_account_opened_at": datetime(2026, 8, 12, 9, 0, 0, tzinfo=timezone.utc),
        "bank_account_opened_source": "customer",
        "bank_account_name": "Chase",

        # TrustOffice integration — looks like it was provisioned and first login happened
        "trustoffice_status": "first_login",
        "trustoffice_user_id": f"user_{uuid.uuid4().hex[:12]}",
        "trustoffice_trust_id": f"trust_{uuid.uuid4().hex[:12]}",
        "trustoffice_set_password_url": None,
        "trustoffice_set_password_expires": None,
        "trustoffice_provisioned_at": "2026-08-05T14:30:00.000000+00:00",
        "trustoffice_password_set_at": "2026-08-05T14:30:00.000000+00:00",
        "trustoffice_first_login_at": "2026-08-05T14:30:00.000000+00:00",
        "trustoffice_last_error": None,
        "trustoffice_retry_at": None,
        "trustoffice_retry_attempts": 0,
        "trustoffice_connect_method": "authenticated_connect",

        # WingPoint reference
        "wingpoint_ref": "WP-20260730-1001",

        # Timestamps
        "created_at": created_at,
        "updated_at": updated_at,
        "completed_at": completed_at,
    }

    # --- Application 2: Smith Family Trust ---
    app2 = {
        "_id": app2_id,
        "id": app2_id,
        "user_id": demo_user_id,
        "token_id": token2_id,

        # Grantor info
        "grantor_first_name": "Margaret",
        "grantor_middle_name": "Elizabeth",
        "grantor_last_name": "Smith",
        "grantor_suffix": "",
        "grantor_full_name": "Margaret Elizabeth Smith",
        "grantor_ssn_encrypted": grantor_ssn_encrypted,

        # Trustee info
        "trustee_first_name": "Margaret",
        "trustee_middle_name": "Elizabeth",
        "trustee_last_name": "Smith",
        "trustee_suffix": "",
        "trustee_full_name": "Margaret Elizabeth Smith",
        "trustee_name": "Margaret Elizabeth Smith",
        "trustee_ssn_encrypted": trustee_ssn_encrypted,

        # WingPoint trustee
        "use_wingpoint_trustee": False,
        "trustee_service_status": "not_applicable",
        "trustee_payment_reminder_sent_at": None,

        # Role
        "role_for_trust": "trustee",

        # Customer contact
        "customer_name": "Margaret Smith",
        "customer_email": "demo@wingpointtrust.com",
        "customer_phone": "(801) 555-0199",

        # Trust details
        "trust_name": "Smith Family Trust",
        "trust_purpose": "family",
        "trust_type": "FAMILY_TRUST",
        "trust_formation_date": "2026-07-30",
        "state_of_domicile": "DE",

        # Mailing address (Delaware)
        "mailing_address_line1": "1209 Orange Street",
        "mailing_address_line2": "",
        "mailing_city": "Wilmington",
        "mailing_state": "DE",
        "mailing_zip": "19801",
        "mailing_county": "New Castle",

        # Entity
        "entity_type": "irrevocable_trust",

        # Workflow state — fully completed
        "status": "completed",

        # EIN + document outputs
        "ein_number": "12-3456789",
        "irs_confirmation_pdf_id": None,
        "irs_confirmation_text": "EIN confirmed via IRS EIN Assistant",
        "declaration_pdf_id": None,
        "certification_pdf_id": None,
        "certification_general_pdf_id": None,
        "certification_banking_pdf_id": None,
        "binder_kit_pdf_id": None,
        "w9_pdf_id": None,
        "ein_source": "automation",
        "ein_obtained_at": completed_at,
        "name_control": "SMIT",
        "ein_issued_date": "2026-07-30",
        "closing_month": "December",
        "confirmation_method": "digital",
        "generation_timestamp": completed_at,
        "error_log": None,

        # Notarization
        "notarized": True,
        "notarized_at": datetime(2026, 8, 5, 16, 0, 0, tzinfo=timezone.utc),
        "notarized_source": "customer",

        # Bank account
        "bank_account_opened": True,
        "bank_account_opened_at": datetime(2026, 8, 15, 11, 30, 0, tzinfo=timezone.utc),
        "bank_account_opened_source": "customer",
        "bank_account_name": "Fidelity",

        # TrustOffice integration
        "trustoffice_status": "first_login",
        "trustoffice_user_id": f"user_{uuid.uuid4().hex[:12]}",
        "trustoffice_trust_id": f"trust_{uuid.uuid4().hex[:12]}",
        "trustoffice_set_password_url": None,
        "trustoffice_set_password_expires": None,
        "trustoffice_provisioned_at": "2026-08-05T16:00:00.000000+00:00",
        "trustoffice_password_set_at": "2026-08-05T16:00:00.000000+00:00",
        "trustoffice_first_login_at": "2026-08-05T16:00:00.000000+00:00",
        "trustoffice_last_error": None,
        "trustoffice_retry_at": None,
        "trustoffice_retry_attempts": 0,
        "trustoffice_connect_method": "authenticated_connect",

        # WingPoint reference
        "wingpoint_ref": "WP-20260730-1002",

        # Timestamps
        "created_at": created_at,
        "updated_at": updated_at,
        "completed_at": completed_at,
    }

    db.trust_applications.insert_many([app1, app2])
    print(f"Created 2 trust applications (both fully completed)")

    # --- Verify ---
    user_count = db.users.count_documents({"email": "demo@wingpointtrust.com"})
    token_count = db.trust_tokens.count_documents({"user_id": demo_user_id})
    app_count = db.trust_applications.count_documents({"user_id": demo_user_id})

    print(f"\n=== Verification ===")
    print(f"  Users: {user_count}")
    print(f"  Tokens: {token_count}")
    print(f"  Applications: {app_count}")

    # Print applications summary
    print(f"\n=== Trust Applications ===")
    for app in db.trust_applications.find({"user_id": demo_user_id}):
        print(f"  {app['trust_name']}")
        print(f"    State: {app['state_of_domicile']}")
        print(f"    EIN: {app['ein_number']}")
        print(f"    Status: {app['status']}")
        print(f"    Created: {app['created_at']}")
        print(f"    Notarized: {app['notarized']}")
        print(f"    Bank: {app['bank_account_opened']} ({app['bank_account_name']})")
        print(f"    TrustOffice: {app['trustoffice_status']}")
        print(f"    Role: {app['role_for_trust']}")
        print()

    print(f"=== Login Credentials ===")
    print(f"  URL: https://wingpointtrust.com/login")
    print(f"  Email: demo@wingpointtrust.com")
    print(f"  Password: {demo_password}")

    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())