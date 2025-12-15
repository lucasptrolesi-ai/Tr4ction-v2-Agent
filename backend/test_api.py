#!/usr/bin/env python
"""Script para testar os endpoints da API"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

endpoints = [
    "/",
    "/founder/trails",
    "/admin/trails",
    "/health"
]

print("=" * 50)
print("TESTANDO API TR4CTION")
print("=" * 50)

all_ok = True
for endpoint in endpoints:
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        status = "OK" if r.status_code == 200 else "FAIL"
        if r.status_code != 200:
            all_ok = False
        print(f"{status} [{r.status_code}] {endpoint}")
        if r.status_code == 200:
            print(f"    -> {r.text[:100]}...")
    except Exception as e:
        all_ok = False
        print(f"ERRO {endpoint} -> {e}")

print("=" * 50)
if all_ok:
    print("TODOS OS ENDPOINTS OK!")
else:
    print("ALGUNS ENDPOINTS FALHARAM!")
    sys.exit(1)
