import json
import os
import subprocess
import re
import ipaddress
import urllib.request

# Global configuration file path (same as used in config.py)
CONFIG_FILE = os.path.expanduser("~/.ubuntu_dns_manager_data.json")


class DNSBackend:
    def __init__(self):
        self.data = self.load_dns_list()

    def _is_valid_ip(self, ip_str):
        """Validates if a string is a valid IPv4 or IPv6 address."""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def load_dns_list(self):
        """Loads DNS list from the JSON file."""
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                # Ensure data is a dict and its values are dictionaries
                if isinstance(data, dict):
                    return {k: v for k, v in data.items() if isinstance(v, dict)}
            return {}
        except Exception:
            return {}

    def save_dns_list(self, data):
        """Saves the current DNS list data."""
        self.data = data
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def import_from_urls(self, urls):
        """Fetches DNS lists from URLs and updates the internal data."""
        new_entries_count = 0
        new_data = self.load_dns_list()

        for url in urls:
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    content = response.read().decode('utf-8')

                    # Process content line by line
                    for line in content.splitlines():
                        # Skip comments and empty lines
                        line = line.strip()
                        if not line or line.startswith(('#', '//')):
                            continue

                        # A line might be just an IP or a name/IP pair
                        parts = re.split(r'\s+', line, maxsplit=1)

                        # Default name is the IP itself
                        ip_str = parts[0]
                        name = ip_str

                        # Try to handle common formats (IP alone or IP/Name pair)
                        if len(parts) > 1 and self._is_valid_ip(parts[1]):
                            # Format is: name IP
                            name = parts[0]
                            ip_str = parts[1]
                        elif not self._is_valid_ip(ip_str) and len(parts) > 1 and self._is_valid_ip(parts[1]):
                            # Format is: Name IP (where Name is not an IP)
                            name = parts[0]
                            ip_str = parts[1]
                        elif self._is_valid_ip(ip_str):
                            # IP is the first part, use IP as name
                            pass
                        else:
                            continue  # Not a valid IP line

                        ip_str = ip_str.strip()

                        # Separate IPv4 and IPv6
                        if self._is_valid_ip(ip_str):
                            ip_type = ipaddress.ip_address(ip_str)

                            # Check if entry already exists (based on name)
                            if name not in new_data:
                                new_data[name] = {
                                    "ipv4": [],
                                    "ipv6": [],
                                    "last_ping": '-',
                                    "last_speed": '-'
                                }

                            # Add IP if not already present in the respective list
                            if ip_type.version == 4:
                                if ip_str not in new_data[name]["ipv4"]:
                                    new_data[name]["ipv4"].append(ip_str)
                                    new_entries_count += 1
                            elif ip_type.version == 6:
                                if ip_str not in new_data[name]["ipv6"]:
                                    new_data[name]["ipv6"].append(ip_str)
                                    new_entries_count += 1

            except Exception as e:
                print(f"Error importing from {url}: {e}")
                continue

        self.save_dns_list(new_data)
        return new_entries_count

    def get_active_connection(self):
        """Gets the active network connection name using nmcli."""
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'NAME,DEVICE,STATE', 'con'], capture_output=True, text=True,
                                    check=True)

            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 3 and parts[2] == 'activated':
                    return parts[0]
            return None
        except Exception as e:
            print(f"Error getting connection info: {e}")
            return None

    def set_dns(self, conn_name, ipv4_list, ipv6_list):
        """Sets DNS for a specific connection using nmcli."""
        ipv4_str = ' '.join(ipv4_list)
        ipv6_str = ' '.join(ipv6_list)

        try:
            # Set method to manual for DNS servers
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv4.method', 'manual'], check=True,
                           capture_output=True)
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv6.method', 'manual'], check=True,
                           capture_output=True)

            # Set DNS servers
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv4.dns', ipv4_str], check=True, capture_output=True)
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv6.dns', ipv6_str], check=True, capture_output=True)

            # Reapply connection
            subprocess.run(['nmcli', 'con', 'up', conn_name], check=True, capture_output=True)

            return True, "DNS updated."
        except subprocess.CalledProcessError as e:
            return False, f"nmcli Error: {e.stderr.strip()}"
        except Exception as e:
            return False, f"An unknown error occurred: {e}"

    def clear_dns(self, conn_name):
        """Resets the DNS settings to automatic (DHCP)."""
        try:
            # Clear manually set DNS
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv4.dns', '""'], check=True, capture_output=True)
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv6.dns', '""'], check=True, capture_output=True)

            # Set method back to auto/dhcp
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv4.method', 'auto'], check=True,
                           capture_output=True)
            subprocess.run(['nmcli', 'con', 'modify', conn_name, 'ipv6.method', 'auto'], check=True,
                           capture_output=True)

            # Reapply connection
            subprocess.run(['nmcli', 'con', 'up', conn_name], check=True, capture_output=True)

            return True, "DNS reset to DHCP."
        except subprocess.CalledProcessError as e:
            return False, f"nmcli Error: {e.stderr.strip()}"
        except Exception as e:
            return False, f"An unknown error occurred: {e}"

    def measure_ping(self, ip):
        """Measures ping latency (average) in milliseconds."""
        try:
            # Use -c 3 for 3 packets, -w 5 for 5 seconds timeout
            # For IPv6, use ping6 command
            cmd = ['ping', '-c', '1', '-W', '1', ip]
            if ipaddress.ip_address(ip).version == 6:
                cmd = ['ping6', '-c', '1', '-W', '1', ip]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)

            # Extract average time (e.g., min/avg/max/mdev = 10.123/15.456/20.789/2.543 ms)
            match = re.search(r'min/avg/max/mdev = [\d\.]+/([\d\.]+)/', result.stdout)
            if match:
                return round(float(match.group(1)))

            return 9999  # Ping failed (Dead)
        except Exception:
            return 9999  # General failure or timeout

    def measure_dig_speed(self, dns_server, domain="google.com"):
        """Measures DNS resolution time (dig speed) in milliseconds."""
        try:
            # Use +time=2 to set a 2-second timeout
            cmd = ['dig', f'@{dns_server}', domain, '+time=2', '+tries=1']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)

            # Extract query time (e.g., Query time: 54 msec)
            match = re.search(r'Query time: (\d+) msec', result.stdout)
            if match:
                return int(match.group(1))

            return 9999  # Dig failed (Dead)
        except Exception:
            return 9999  # General failure or timeout