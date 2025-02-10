# Web-shot
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Status](https://img.shields.io/badge/Status-Active-green)
![License](https://img.shields.io/badge/License-MIT-brightgreen)

📸 | **Takes a screenshot of every domain/link provided and saves it in /screenshots Options to choose full page picture with highly customizable options**
<details> 
<summary>𝐅𝐮𝐥𝐥 𝐏𝐚𝐠𝐞 𝐒𝐜𝐫𝐞𝐞𝐧𝐬𝐡𝐨𝐭 𝐏𝐫𝐞𝐯𝐢𝐞𝐰</summary>
<img src="https://github.com/user-attachments/assets/623b4eaf-7a9b-450e-ac53-babf6a2b8963">
</details> 
<details> 
<summary>𝐇𝐚𝐥𝐟 𝐏𝐚𝐠𝐞 𝐒𝐜𝐫𝐞𝐞𝐧𝐬𝐡𝐨𝐭 𝐏𝐫𝐞𝐯𝐢𝐞𝐰</summary>
<img src="https://github.com/user-attachments/assets/dcf0cb90-c420-4c0d-866f-b77dd7e2dbc2">
</details> 

## Table of Contents
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [Terminal Output For Each Domain](#terminal-output-for-each-processed-website)
- [Config File](#config-file)
- [Python 3.12+ Pip Fix](#python-312-pip-fix)

## Features
- **Fast & Accurate**: Captures full-page screenshots using Playwright.
- **Highly Configurable**: Customize options via `config.yaml`:
  - Viewport size, image format (PNG/JPEG), quality, dark mode.
  - Network options: Block images, stylesheets, JavaScript.
  - Proxy support and custom headers.
  - Naming schemes: Full URL, domain-only, or custom patterns.
- **Concurrency**: Process multiple websites concurrently for speed.
- **Professional Terminal Output**:
  - Color-coded status codes (2xx = Green, 3xx = Yellow, 4xx/5xx = Red).
  - Clear, customizable output templates.
- **Logging**: Option to log output to a file.

## Setup
**1. Clone Repository**
```
git clone https://github.com/zebbern/web-shot
cd web-shots
```
**2. Install Dependesies**
```
pip install playwright pyyaml colorama
playwright install
```
## Usage
1. **Prepare Your Target List**  
   Create a file named `domains.txt` with one domain per line.

2. **Customize `config.yaml`**  
   Adjust any settings (e.g., viewport size, dark mode, naming scheme) in the `config.yaml` file.

3. **Run the Script**  
   Execute the script to start capturing screenshots:
   ```bash
   python webshot.py
   ```

## Terminal output for each processed website:
```
[1/10] [ 200 ] https://example.com https___github_com_20250310153045.png
[2/10] [ 200 ] https://example.com https___example2_com_20250310153045.png
[3/10] [ 200 ] https://example.com https___test3_com_20250310153045.png
```

## Config File
`config.yaml`
```yaml
general:
  input_file: "domains.txt"         # File with one domain per line.
  output_dir: "screenshots"         # Directory to save screenshots.
  format: "png"                     # Image format: "png" or "jpeg".
  clear_terminal: true              # Clear the terminal when starting.
  verbose: false                    # Verbose output (optional).
  log_to_file: false                # If true, log output to a file.
  log_file: ""                      # Log file path (e.g., "screenshot.log").
  naming_scheme: "custom"         # Options: "full_url", "domain", "custom"
  custom_name_pattern: "{url}"  # Only used if naming_scheme is "custom"

screenshot:
  width: 1920                     # Viewport width in pixels.
  height: 1080                    # Viewport height in pixels.
  scale_factor: 1                 # Device scale factor.
  dark_mode: true                # Use dark mode for rendering.
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
  full_page: true                 # Take a full-page screenshot.
  delay: 0                        # Delay (in seconds) after page load before screenshot.
  quality: 80                     # JPEG quality (only used if format is "jpeg").
  background_color: ""            # If set (e.g., "#ffffff"), sets the page background color.

concurrency:
  use_concurrent: true            # Process domains concurrently.
  max_workers: 4                  # Maximum number of concurrent browser instances.

timeouts:
  navigation_timeout: 15000       # Navigation timeout in milliseconds.
  wait_until: "load"              # When to consider navigation done ("load", "domcontentloaded", "networkidle").

network:
  block_images: false             # Block image resources.
  block_stylesheets: false        # Block CSS resources.
  block_javascript: false         # Block JavaScript resources.

advanced:
  custom_headers: {}              # Custom HTTP headers (as a mapping).
  proxy: ""                       # Proxy server (e.g., "http://127.0.0.1:8080").

terminal:
  color_success: "GREEN"          # Color for 2xx status codes.
  color_warning: "YELLOW"         # Color for 3xx status codes.
  color_error: "RED"              # Color for 4xx/5xx status codes.
  color_default: "WHITE"          # Default color.
  output_template: "[{current}/{total}] [{status}] {url} {filename}"  # Template for terminal output.

```


## Python 3.12+ Pip Fix:
### Create and Activate a Virtual Environment
#### For Linux/macOS:
```
python3 -m venv venv && source venv/bin/activate
```
#### For Windows:
```
python -m venv venv && .\venv\Scripts\activate
```
