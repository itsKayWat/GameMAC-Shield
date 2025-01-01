import subprocess
import sys

def install_requirements():
    requirements = [
        'tkinter',
        'colorama',
        'elevate',
        'pathlib'
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except:
            print(f"Failed to install {package}")
    
    print("\nInstallation complete!")

if __name__ == "__main__":
    install_requirements()