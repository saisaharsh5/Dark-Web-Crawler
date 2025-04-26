import os
import subprocess

# Correct path to wkhtmltoimage
WKHTMLTOIMAGE_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe"

# Add wkhtmltoimage to the system PATH
os.environ["PATH"] += os.pathsep + os.path.dirname(WKHTMLTOIMAGE_PATH)

def capture_screenshot(url, output_filename):
    proxy = "socks5://127.0.0.1:9050"  # Tor Proxy

    # Command formatted correctly for Windows
    command = [
        WKHTMLTOIMAGE_PATH, 
        "--proxy", proxy, 
        url, 
        output_filename
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ Screenshot saved as {output_filename}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Screenshot failed. Error: {e.stderr}")

# Example Usage
tor_site = "http://x5qddgzmfzs36gnojvvwgb7espqatlosymbhv4b4kgtyhs64wzgnhqyd.onion "
capture_screenshot(tor_site, "screenshot.png")
