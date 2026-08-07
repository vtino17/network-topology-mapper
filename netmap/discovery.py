import subprocess
import sys
import re
import socket
import ipaddress

MAX_PING_HOSTS = 4096

# `arp -a` prints two shapes:
#   Linux/BSD  ? (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on wlan0
#   Windows      192.168.1.1   aa-bb-cc-dd-ee-ff   dynamic
# The IP may be parenthesised and followed by "at", and the MAC octets may be
# separated by either colons or hyphens.
ARP_ENTRY = re.compile(
    r"\(?(\d{1,3}(?:\.\d{1,3}){3})\)?\s+(?:at\s+)?"
    r"([0-9a-f]{2}(?:[:-][0-9a-f]{2}){5})",
    re.IGNORECASE,
)


def parse_arp_output(output, subnet=None):
    """Extract host entries from `arp -a` output.

    Split out from arp_scan so the parsing can be tested without running arp.
    """
    results = []
    for line in output.splitlines():
        match = ARP_ENTRY.search(line)
        if not match:
            # Skips headers and incomplete entries such as
            # "? (192.168.1.5) at <incomplete> on wlan0".
            continue
        ip = match.group(1)
        if subnet and not _in_subnet(ip, subnet):
            continue
        mac = match.group(2).replace("-", ":").lower()
        results.append({"ip": ip, "mac": mac, "hostname": resolve_hostname(ip)})
    return results


def _in_subnet(ip, subnet):
    """Best-effort /24 match on the first three octets.

    arp_scan took a subnet argument and ignored it, so callers asking for one
    network were handed the machine's entire ARP cache.
    """
    try:
        prefix = ".".join(subnet.split("/")[0].split(".")[:3])
        return ip.startswith(prefix + ".")
    except (AttributeError, IndexError):
        return True


def arp_scan(subnet=None):
    try:
        output = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    return parse_arp_output(output, subnet)

def resolve_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        return None

def ping_sweep(subnet, count=1):
    network = ipaddress.ip_network(subnet, strict=False)
    if network.version != 4:
        raise ValueError("ping_sweep currently supports IPv4 networks only")
    host_count = max(0, network.num_addresses - (0 if network.prefixlen >= 31 else 2))
    if host_count > MAX_PING_HOSTS:
        raise ValueError(
            f"subnet expands to {host_count} hosts; maximum is {MAX_PING_HOSTS}"
        )
    results = []
    for address in network.hosts():
        ip = str(address)
        param = "-n" if sys.platform == "win32" else "-c"
        try:
            r = subprocess.run(["ping", param, str(count), ip], capture_output=True, timeout=5)
            if r.returncode == 0:
                results.append(ip)
        except subprocess.TimeoutExpired:
            pass
    return results
