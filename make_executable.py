#!/usr/bin/env python3
"""
Make scripts executable
"""
import os
import stat

scripts = [
    "scripts/version/dynamic-version.py",
    "scripts/version/generate-build-metadata.sh",
    "scripts/validate-cicd-setup.sh",
]

for script in scripts:
    if os.path.exists(script):
        # Get current permissions
        current_permissions = os.stat(script).st_mode
        # Add execute permissions for owner, group, and others
        new_permissions = (
            current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        os.chmod(script, new_permissions)
        print(f"✅ Made {script} executable")
    else:
        print(f"❌ {script} not found")

print("🎉 Script permissions updated!")
