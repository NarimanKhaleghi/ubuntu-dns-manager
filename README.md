[English](README.md "null") | [فارسی](docs/README_FA.md "null")

# Ubuntu DNS Manager Pro - Advanced Ubuntu DNS Management Tool

`Ubuntu DNS Manager Pro` is a Tkinter-based Graphical User Interface (GUI) for managing, speed testing, and applying DNS servers on the Ubuntu operating system (and Debian/Ubuntu-based distributions that use `nmcli`). This tool allows users to import external DNS lists, measure server performance (Ping and Dig speed), and automatically remove slow or invalid servers.

**Note:** This program requires **root (sudo)** access to apply network settings.

## Key Features

- **Full IPv4 and IPv6 Support:** Capability to import, test, and apply both types of IP addresses.
    
- **Performance Testing:** Accurate measurement of latency (Ping) and DNS response speed (Dig).
    
- **Instant Removal (Fail-Fast Auto-Clean):** DNS servers that exceed the defined limits for Ping or response speed during testing are immediately removed from the list.
    
- **DNS List Management:** Import new lists via Dynamic URLs.
    
- **Advanced Sorting:** Sort the table by name, IP, Ping, and Speed (with the ability to handle non-numeric values and proper numerical sorting).
    
- **Multilingual Support:** Includes Persian (Farsi), English, Chinese, and Russian.
    
- **Easy Configuration Application:** Apply desired DNS settings with just one click using the `nmcli` tool.
    

## Project Structure

| File/Directory | Description |
|---|---|
| `src/main.py` | The main entry point of the program. |
| `src/gui.py` | The core of the user interface (Tkinter), manages user interactions, sorting, and data display. |
| `src/backend.py` | The core program logic, includes test functions (Ping/Dig), IP validation (IPv4/IPv6), and `nmcli` management. |
| `src/config.py` | Manages saving and loading user settings (such as language, update links, and auto-clean limits). |
| `src/lang.py` | Translation file containing multilingual texts. |
| `install.sh` | Installation script for system preparation, handling dependencies, and creating a shortcut. |
| `README.md` | This file. |

## Installation and Execution Guide (Manual)

1. **Install System Dependencies:**
    
    ```
    sudo apt update
    sudo apt install python3-tk bind9-dnsutils iputils-ping curl python3-pip fonts-noto-core
    ```
    
2. **Install Python Libraries (for Persian text support):**
    
    ```
    pip3 install arabic-reshaper python-bidi
    ```
    
    _If you encounter errors, use the `--break-system-packages` flag._
    
3. **Execution:**
    
    ```
    sudo python3 src/main.py
    ```
    

**It is recommended to run the `install.sh` script for easy and complete installation.**


# src/ - Program Core Logic

The `src/` directory contains all the Python source files that form the logic and user interface of `Ubuntu DNS Manager Pro`.

## File Summary

### `main.py`

This file acts as the program's starting point. Its responsibility is solely to import necessary modules, set up the initial environment, and call the main UI class (`DNSApp`).

### `gui.py`

The main user interface classes (`DNSApp` and `ConfigDialog`) are defined in this file.

- **Main Tasks:** Creating Tkinter windows and widgets, managing user interactions (button clicks, row selections), executing sorting logic (based on numerical and textual values), and displaying network status.
    
- **Special Attention:** The **Instant Removal (Fail-Fast)** logic is implemented in the `_test_worker` method, so that if a DNS server exceeds the limits defined in the settings during Ping or Dig testing, it is immediately removed from the list via the `_delete_row_safe` method.
    

### `backend.py`

This file contains all the backend logic and interaction with the operating system.

- **DNS List Management:** The `load_dns_list` and `save_dns_list` functions for persisting data to a JSON file on disk.
    
- **IP Validation:** Uses the `ipaddress` library to validate and differentiate **IPv4 and IPv6** addresses.
    
- **Network Control:** The `get_active_connection`, `set_dns`, and `clear_dns` functions for interfacing with `nmcli` and applying DNS settings.
    
- **Benchmarking:** The `measure_ping` function (which uses `ping6` for IPv6) and `measure_dig_speed` function for performance measurement.
    

### `config.py`

Manages user-saved settings. Includes:

- User Interface language.
    
- List of Dynamic URLs for importing DNS servers.
    
- Allowed limits for Ping and Dig speed for the auto-clean logic.
    

### `lang.py`

A simple dictionary for managing multilingual text strings and providing translations for the user interface.