#!/usr/bin/env python3
import os
import sys
import asyncio
import yaml
import re
from datetime import datetime
from urllib.parse import urlparse
import logging

from colorama import init, Fore, Style
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Initialize colorama
init(autoreset=True)

# --- Load Configuration (assume config.yaml exists) ---
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

# --- Setup Logging ---
# If log_to_file is enabled, log messages go only to file (no stream handler).
log_to_file = config.get("general", {}).get("log_to_file", False)
if log_to_file:
    log_file = config.get("general", {}).get("log_file", "screenshot.log")
    logging.basicConfig(filename=log_file,
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    # Remove any stream handlers so logging doesn't output to console.
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
         if isinstance(handler, logging.StreamHandler):
             root_logger.removeHandler(handler)
else:
    # If file logging is not enabled, add a NullHandler so logging calls don't output.
    logging.getLogger().addHandler(logging.NullHandler())

# --- Terminal Color Mapping ---
COLOR_MAP = {
    "BLACK": Fore.BLACK,
    "RED": Fore.RED,
    "GREEN": Fore.GREEN,
    "YELLOW": Fore.YELLOW,
    "BLUE": Fore.BLUE,
    "MAGENTA": Fore.MAGENTA,
    "CYAN": Fore.CYAN,
    "WHITE": Fore.WHITE
}

def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")

def sanitize_filename(url):
    # Replace all non-alphanumeric characters with underscores.
    return re.sub(r'[^\w\-_\.]', '_', url)

def get_status_color(status, terminal_conf):
    # Use custom colors from terminal config.
    if status is None:
        return COLOR_MAP.get(terminal_conf.get("color_default", "WHITE").upper(), Fore.WHITE)
    if 200 <= status < 300:
        return COLOR_MAP.get(terminal_conf.get("color_success", "GREEN").upper(), Fore.GREEN)
    elif 300 <= status < 400:
        return COLOR_MAP.get(terminal_conf.get("color_warning", "YELLOW").upper(), Fore.YELLOW)
    elif status >= 400:
        return COLOR_MAP.get(terminal_conf.get("color_error", "RED").upper(), Fore.RED)
    else:
        return COLOR_MAP.get(terminal_conf.get("color_default", "WHITE").upper(), Fore.WHITE)

def build_filename(url, file_format, naming_scheme, custom_pattern):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    if naming_scheme == "full_url":
        sanitized = sanitize_filename(url)
        return f"{sanitized}_{timestamp}.{file_format}"
    elif naming_scheme == "domain":
        parsed = urlparse(url)
        domain = sanitize_filename(parsed.netloc)
        return f"{domain}_{timestamp}.{file_format}"
    elif naming_scheme == "custom":
        parsed = urlparse(url)
        domain = sanitize_filename(parsed.netloc)
        # custom_pattern can use placeholders: {url}, {domain}, {timestamp}
        return f"{custom_pattern.format(url=sanitize_filename(url), domain=domain, timestamp=timestamp)}.{file_format}"
    else:
        # Fallback to full_url naming
        sanitized = sanitize_filename(url)
        return f"{sanitized}_{timestamp}.{file_format}"

async def process_domain(domain, index, total, config, semaphore):
    async with semaphore:
        async with async_playwright() as p:
            browser = None
            try:
                # --- Launch Browser with Optional Proxy ---
                proxy = config.get("advanced", {}).get("proxy", "")
                launch_args = {"headless": True}
                if proxy:
                    launch_args["proxy"] = {"server": proxy}
                browser = await p.chromium.launch(**launch_args)
                
                # --- Retrieve Screenshot Settings ---
                screenshot_conf = config.get("screenshot", {})
                viewport = {
                    "width": screenshot_conf.get("width", 1920),
                    "height": screenshot_conf.get("height", 1080)
                }
                device_scale_factor = screenshot_conf.get("scale_factor", 1)
                user_agent = screenshot_conf.get("user_agent", 
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
                dark_mode = screenshot_conf.get("dark_mode", False)
                color_scheme = "dark" if dark_mode else "light"
                full_page = screenshot_conf.get("full_page", True)
                delay = screenshot_conf.get("delay", 0)
                quality = screenshot_conf.get("quality", None)  # Only used for JPEG
                bg_color = screenshot_conf.get("background_color", "")
                
                # --- Retrieve Advanced Settings ---
                advanced_conf = config.get("advanced", {})
                custom_headers = advanced_conf.get("custom_headers", {})
                
                # --- Create Browser Context ---
                context = await browser.new_context(
                    viewport=viewport,
                    device_scale_factor=device_scale_factor,
                    user_agent=user_agent,
                    color_scheme=color_scheme,
                    extra_http_headers=custom_headers
                )
                
                # --- Setup Network Routing ---
                network_conf = config.get("network", {})
                block_images = network_conf.get("block_images", False)
                block_stylesheets = network_conf.get("block_stylesheets", False)
                block_javascript = network_conf.get("block_javascript", False)
                if block_images or block_stylesheets or block_javascript:
                    async def route_handler(route, request):
                        rt = request.resource_type
                        if block_images and rt == "image":
                            await route.abort()
                        elif block_stylesheets and rt == "stylesheet":
                            await route.abort()
                        elif block_javascript and rt == "script":
                            await route.abort()
                        else:
                            await route.continue_()
                    await context.route("**/*", route_handler)
                
                page = await context.new_page()
                timeouts_conf = config.get("timeouts", {})
                navigation_timeout = timeouts_conf.get("navigation_timeout", 15000)
                wait_until = timeouts_conf.get("wait_until", "load")
                
                # --- Ensure URL Has a Scheme ---
                url = domain if domain.startswith(("http://", "https://")) else "http://" + domain
                response = await page.goto(url, timeout=navigation_timeout, wait_until=wait_until)
                
                if delay > 0:
                    await asyncio.sleep(delay)
                status = response.status if response else None

                # --- Set Background Color if Specified ---
                if bg_color:
                    await page.evaluate(f"document.body.style.backgroundColor = '{bg_color}';")
                
                # --- Prepare Output Directory & Filename ---
                output_dir = config.get("general", {}).get("output_dir", "screenshots")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                file_format = config.get("general", {}).get("format", "png").lower()
                naming_scheme = config.get("general", {}).get("naming_scheme", "full_url")
                custom_pattern = config.get("general", {}).get("custom_name_pattern", "{domain}_{timestamp}")
                output_filename = build_filename(url, file_format, naming_scheme, custom_pattern)
                output_path = os.path.join(output_dir, output_filename)
                
                # --- Take Screenshot ---
                screenshot_kwargs = {"path": output_path, "full_page": full_page, "type": file_format}
                if file_format == "jpeg" and quality:
                    screenshot_kwargs["quality"] = quality
                await page.screenshot(**screenshot_kwargs)
                
                await context.close()
                await browser.close()
                
                # --- Terminal Output Using Custom Template ---
                terminal_conf = config.get("terminal", {})
                output_template = terminal_conf.get("output_template", "[{current}/{total}] [{status}] {url} {filename}")
                status_str = f"{status}" if status else "NoResp"
                status_color = get_status_color(status, terminal_conf)
                message = output_template.format(current=index,
                                                 total=total,
                                                 status=f"{status_color}{status_str}{Style.RESET_ALL}",
                                                 url=url,
                                                 filename=output_filename)
                # Print only once to terminal.
                print(message)
                # Log to file if enabled.
                logging.info(message)
            except PlaywrightTimeoutError:
                msg = f"[{index}/{total}] [{Fore.RED}Timeout{Style.RESET_ALL}] {domain} - Timeout after {navigation_timeout} ms"
                print(msg)
                logging.error(msg)
                if browser:
                    await browser.close()
            except Exception as e:
                msg = f"[{index}/{total}] [{Fore.RED}Error{Style.RESET_ALL}] {domain} - {e}"
                print(msg)
                logging.error(msg)
                if browser:
                    await browser.close()

async def main():
    if config.get("general", {}).get("clear_terminal", True):
        clear_terminal()
    
    input_file = config.get("general", {}).get("input_file", "domains.txt")
    if not os.path.exists(input_file):
        print(f"{Fore.RED}Input file '{input_file}' not found. Please create it with one domain per line.")
        sys.exit(1)
    
    with open(input_file, "r") as f:
        domains = [line.strip() for line in f if line.strip()]
    
    total = len(domains)
    print(f"{Fore.MAGENTA}Starting advanced screenshot capture for {total} domain(s)...{Style.RESET_ALL}")
    logging.info(f"Starting advanced screenshot capture for {total} domain(s)...")
    
    concurrency_conf = config.get("concurrency", {})
    use_concurrent = concurrency_conf.get("use_concurrent", True)
    max_workers = concurrency_conf.get("max_workers", 4)
    semaphore = asyncio.Semaphore(max_workers) if use_concurrent else asyncio.Semaphore(1)
    
    tasks = [process_domain(domain, idx, total, config, semaphore)
             for idx, domain in enumerate(domains, start=1)]
    await asyncio.gather(*tasks)
    print(f"{Fore.MAGENTA}Processing complete. {total} domain(s) processed.{Style.RESET_ALL}")
    logging.info(f"Processing complete. {total} domain(s) processed.")

if __name__ == "__main__":
    asyncio.run(main())