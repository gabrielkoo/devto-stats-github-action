#!/usr/bin/env python3
"""
Compare results between shell and Python versions of fetch_stats
"""

import json
import subprocess
import sys
from pathlib import Path
import shutil

def backup_data():
    """Backup current data"""
    if Path("data").exists():
        if Path("data_backup").exists():
            shutil.rmtree("data_backup")
        shutil.copytree("data", "data_backup")
        print("✅ Backed up current data to data_backup/")

def restore_data():
    """Restore data from backup"""
    if Path("data_backup").exists():
        if Path("data").exists():
            shutil.rmtree("data")
        shutil.copytree("data_backup", "data")
        print("✅ Restored data from backup")

def run_script(script_name):
    """Run a script and capture its output"""
    print(f"\n🔄 Running {script_name}...")
    try:
        if script_name.endswith('.py'):
            result = subprocess.run(['python3', script_name],
                                  capture_output=True, text=True, timeout=60)
        else:
            result = subprocess.run([f'./{script_name}'],
                                  capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            return True
        else:
            print(f"❌ {script_name} failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def compare_json_files(file1, file2):
    """Compare two JSON files"""
    try:
        with open(file1) as f1, open(file2) as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        if data1 == data2:
            return True, "Files are identical"
        else:
            # Find differences
            differences = []
            if isinstance(data1, dict) and isinstance(data2, dict):
                for key in set(data1.keys()) | set(data2.keys()):
                    if key not in data1:
                        differences.append(f"Key '{key}' missing in first file")
                    elif key not in data2:
                        differences.append(f"Key '{key}' missing in second file")
                    elif data1[key] != data2[key]:
                        differences.append(f"Key '{key}': {data1[key]} != {data2[key]}")

            return False, "; ".join(differences[:5])  # Limit to first 5 differences

    except Exception as e:
        return False, f"Error comparing files: {e}"

def main():
    print("🔍 Comparing Shell vs Python fetch_stats implementations")
    print("=" * 60)

    # Backup current data
    backup_data()

    try:
        # Test shell version
        print("\n📋 Testing Shell Version (fetch_stats.sh)")
        if Path("data").exists():
            shutil.rmtree("data")

        shell_success = run_script("fetch_stats.sh")
        if shell_success:
            # Copy results
            if Path("data_shell").exists():
                shutil.rmtree("data_shell")
            shutil.copytree("data", "data_shell")
            print("✅ Shell results saved to data_shell/")

        # Test Python version
        print("\n🐍 Testing Python Version (fetch_stats.py)")
        if Path("data").exists():
            shutil.rmtree("data")

        python_success = run_script("fetch_stats.py")
        if python_success:
            # Copy results
            if Path("data_python").exists():
                shutil.rmtree("data_python")
            shutil.copytree("data", "data_python")
            print("✅ Python results saved to data_python/")

        # Compare results
        if shell_success and python_success:
            print("\n🔍 Comparing Results")
            print("-" * 30)

            # Compare account.json
            account_match, account_diff = compare_json_files(
                "data_shell/account.json", "data_python/account.json"
            )
            print(f"account.json: {'✅ Match' if account_match else '❌ Differ'}")
            if not account_match:
                print(f"  Differences: {account_diff}")

            # Compare top_articles.json
            top_match, top_diff = compare_json_files(
                "data_shell/top_articles.json", "data_python/top_articles.json"
            )
            print(f"top_articles.json: {'✅ Match' if top_match else '❌ Differ'}")
            if not top_match:
                print(f"  Differences: {top_diff}")

            # Compare article files
            shell_articles = set(f.name for f in Path("data_shell/articles").glob("*.json"))
            python_articles = set(f.name for f in Path("data_python/articles").glob("*.json"))

            if shell_articles == python_articles:
                print(f"Article files: ✅ Same set of {len(shell_articles)} files")

                # Compare content of each article file
                mismatches = 0
                for filename in shell_articles:
                    match, diff = compare_json_files(
                        f"data_shell/articles/{filename}",
                        f"data_python/articles/{filename}"
                    )
                    if not match:
                        mismatches += 1
                        if mismatches <= 3:  # Show first 3 mismatches
                            print(f"  {filename}: ❌ Differ - {diff}")

                if mismatches == 0:
                    print("  All article files: ✅ Content matches")
                elif mismatches > 3:
                    print(f"  ... and {mismatches - 3} more files differ")
            else:
                print(f"Article files: ❌ Different sets")
                print(f"  Shell only: {shell_articles - python_articles}")
                print(f"  Python only: {python_articles - shell_articles}")

            # Overall result
            overall_success = account_match and top_match and shell_articles == python_articles and mismatches == 0
            print(f"\n🎯 Overall Result: {'✅ PASS - Both implementations produce identical results' if overall_success else '❌ FAIL - Results differ'}")

        else:
            print("\n❌ Cannot compare - one or both scripts failed")

    finally:
        # Restore original data
        restore_data()

        # Clean up temporary directories
        for temp_dir in ["data_shell", "data_python"]:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()