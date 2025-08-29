#!/usr/bin/env python3
"""
Docker healthcheck script for blacklist app
"""
import requests
import sys
import os


def main():
    try:
        port = os.environ.get("PORT", "2542")
        url = f"http://localhost:{port}/health"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data.get("status") == "healthy":
            print("Health check passed")
            sys.exit(0)
        else:
            print(f"Health check failed: {data}")
            sys.exit(1)

    except Exception as e:
        print(f"Health check error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
