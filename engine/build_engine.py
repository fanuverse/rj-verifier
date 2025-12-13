import subprocess
import sys
import os
import shutil

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, 'dist')
    main_script = os.path.join(base_dir, 'main.py')
    
    if os.path.exists(dist_dir):
        try:
            shutil.rmtree(dist_dir)
        except Exception as e:
            print(f"Warning: Could not clean dist folder: {e}")
    
    os.makedirs(dist_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--include-package=k12",
        "--include-package-data=k12",
        f"--output-dir={dist_dir}",
        "--output-filename=rj_engine.exe",
        "--assume-yes-for-downloads",
        main_script
    ]
    
    print(f"Building engine from: {main_script}")
    print("Command:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\n\n[SUCCESS] Engine built successfully!")
        print(f"Path: {os.path.join(dist_dir, 'rj_engine.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\n\n[ERROR] Build failed with exit code {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    build()
