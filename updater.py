import os
import shutil
import sys
import time
import subprocess

def main():
    if len(sys.argv) != 3:
        print("Usage: updater.exe <old_exe_path> <new_exe_path>")
        time.sleep(3)
        return

    old_path = sys.argv[1]
    new_path = sys.argv[2]

    try:
        time.sleep(2)  # Give the original app time to close

        # Replace the old .exe with the new one
        shutil.copy2(new_path, old_path)

        # Relaunch the updated app
        subprocess.Popen([old_path])

    except Exception as e:
        print(f"Update failed: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
