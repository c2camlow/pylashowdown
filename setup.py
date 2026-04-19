import sys
import platform
import subprocess
import os

if platform.system() != "Windows" or "microsoft" in platform.uname()[3].lower():
    print("\n" + "!"*50)
    print("  ERROR: This version of PylaAI is for WINDOWS ONLY.")
    print("  Mac or Linux detected. Please use the Universal branch.")
    print("!"*50 + "\n")
    sys.exit(1)

# Fixes missing setuptools
def bootstrap():
    if os.environ.get("PYLAAI_BOOTSTRAP") == "1": return
    try:
        import setuptools
    except ImportError:
        print("\nDetected missing core tools. Stabilizing environment...")
        os.environ["PYLAAI_BOOTSTRAP"] = "1"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
        subprocess.run([sys.executable] + sys.argv)
        sys.exit(0) 

if any(cmd in sys.argv for cmd in ["install", "develop"]):
    bootstrap()

from setuptools import setup, find_packages

def force_install(reqs, no_deps=False):
    cmd = [sys.executable, "-m", "pip", "install"]
    if no_deps: cmd += ["--force-reinstall", "--no-deps"]
    subprocess.check_call(cmd + reqs)

def get_gpu_data():
    """Detects exact NVIDIA/AMD/Intel architecture for Windows."""
    # NVIDIA cards Check
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader,nounits"],
            encoding='utf-8', stderr=subprocess.DEVNULL).strip()
        name, cc = output.split(', ')
        return "nvidia", float(cc), name
    except: pass

    # AMD/Intel cards Check
    try:
        wmic = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "name"], encoding='utf-8')
        if "Intel" in wmic: return "intel", 0.0, "Intel HD/Arc Graphics"
        if "AMD" in wmic or "Radeon" in wmic: return "amd_windows", 0.0, "AMD Radeon"
    except: pass

    return "cpu", 0.0, "Generic CPU"

def ask_user(prompt_text):
    print(f"\n{prompt_text} (Y/N): ", end='', flush=True)
    response = sys.stdin.readline().strip().lower()
    return response in ['y', 'yes']

def setup_pyla():
    print("\n" + "="*50 + "\n   PylaAi - Windows Setup   \n" + "="*50)
    
    # installing must have Pytorch CPU
    force_install(["torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cpu"])

    # installing some must have dependencies
    print("Installing Core Dependencies...")
    base_reqs = [
        "customtkinter>=5.2.0", "toml>=0.10.2", "Pillow>=10.0.0", "discord.py>=2.3.2",
        "opencv-python==4.8.0.76", "requests", "ultralytics", "aiohttp", "easyocr", 
        "google-play-scraper"
    ]
    force_install(base_reqs)

    target, ver, name = get_gpu_data()
    status_pytorch, status_accel = "CPU Edition", "N/A"
    
    # We will use this flag to check if we need the standard CPU onnxruntime
    onnx_installed = False

    # --- THE CHOICE BRANCHES ---
    
    # NVIDIA BRANCH (Series 10-50)
    if target == "nvidia":
        print(f"\n NVIDIA: {name} detected.")
        if ask_user("Install NVIDIA CUDA acceleration? (takes more storage but gives you more ips, about 2GB)"):
            if ver >= 10.0: # 50-Series Blackwell
                torch_cmd = ["--pre", "torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/nightly/cu128"]
                status_accel = "CUDA 12.8 (Blackwell)"
            elif ver >= 8.9: # 40-Series Ada
                torch_cmd = ["torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cu124"]
                status_accel = "CUDA 12.4 (Ada)"
            else: # 10/20/30-Series
                torch_cmd = ["torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cu121"]
                status_accel = "CUDA 12.1 (Standard)"
            
            force_install(torch_cmd)
            force_install(["onnxruntime-gpu"])
            onnx_installed = True
            status_pytorch = "CUDA Edition"

    # INTEL BRANCH (OpenVINO)
    elif target == "intel":
        print(f"\n Intel: {name} detected.")
        if ask_user("Install Intel OpenVINO acceleration? (best for Intel Arc/Integrated GPUs)"):
            force_install(["onnxruntime-openvino"])
            onnx_installed = True
            status_pytorch = "OpenVINO Edition"
            status_accel = "OpenVINO"

    # AMD BRANCH (DirectML)
    elif "amd" in target:
        print(f"\n AMD: {name} detected.")
        if ask_user("Install AMD DirectML acceleration?"):
            force_install(["onnxruntime-directml"])
            onnx_installed = True
            status_pytorch = "DirectML Edition"
            status_accel = "DirectML"

    # FALLBACK BRANCH (If user skipped acceleration or has a generic CPU)
    if not onnx_installed:
        print("\n Installing standard CPU ONNX Runtime...")
        force_install(["onnxruntime"])
        status_accel = "Standard CPU"

    # some conflict fixes
    print("\n Finalizing and Repairing Conflicts...")
    force_install(["numpy<2.0.0"], no_deps=True)
    force_install(["adbutils==2.12.0", "av==12.3.0"])
    force_install(["git+https://github.com/leng-yue/py-scrcpy-client.git@v0.5.0"], no_deps=True)

    # the setup completes
    os.system('cls')
    print("="*50)
    print("            SETUP COMPLETED!")
    print("="*50)
    print(f"  - GPU Detected:     {name}")
    print(f"  - PyTorch:          {status_pytorch}")
    print(f"  - Accel Status:     {status_accel}")
    print("="*50 + "\n")

setup(
    name="PylaAI", version="1.0.0",
    packages=find_packages(exclude=["api", "cfg", "models", "typization"]),
    install_requires=[]
)

if any(cmd in sys.argv for cmd in ["install", "develop"]):
    try: setup_pyla()
    except Exception as e: print(f"\n[ERROR] {e}"); sys.exit(1)