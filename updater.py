import os
import sys
import time
import shutil
import subprocess

def main():
    old_path = sys.argv[1]  # original app path
    new_path = sys.argv[2]  # path to downloaded update

    time.sleep(2)  # give the main app time to close

    for i in range(10):
        try:
            os.remove(old_path)
            shutil.move(new_path, old_path)
            break
        except PermissionError:
            time.sleep(1)

    subprocess.Popen([old_path])
    sys.exit()

if __name__ == "__main__":
    main()
