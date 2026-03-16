#!/usr/bin/env python3
"""
Local code quality checker - runs the same checks as CI.
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*50}")
    print(f"🔍 {description}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Run all code quality checks."""
    print("🧹 Running Local Code Quality Checks")
    print("(Same checks that run in GitHub Actions)")
    
    paths = "src/ tests/ point_slice_studio_gui.py point_slice_studio_cli.py"
    checks = [
        (f"black --check --diff {paths}", "Code Formatting Check"),
        (f"flake8 {paths} --count --select=E9,F63,F7,F82,F401,F841 --show-source --statistics", "Critical Linting Issues"),
        (f"flake8 {paths} --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics", "Style Warnings"),
    ]
    
    all_passed = True
    
    for cmd, description in checks:
        passed = run_command(cmd, description)
        if not passed and ("Critical" in description or "Formatting" in description):
            all_passed = False
    
    print(f"\n{'='*50}")
    
    if all_passed:
        print("🎉 All checks passed! Ready to push.")
        return 0
    else:
        print("🚨 Some checks failed. Fix issues before pushing.")
        print("\nTo auto-fix formatting: black src/ tests/")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 