import subprocess
import re
import socket

def arp_scan(subnet):
    results = []
    try:
        output = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return results
    for line in output.splitlines():
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]{17,})", line, re.IGNORECASE)
        if match:
            ip = match.group(1)
            mac = match.group(2).replace("-", ":")
            results.append({"ip": ip, "mac": mac, "hostname": resolve_hostname(ip)})
    return results

def resolve_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        return None

def ping_sweep(subnet, count=1):
    base = ".".join(subnet.split(".")[:3])
    results = []
    for i in range(1, 255):
        ip = f"{base}.{i}"
        param = "-n" if sys.platform == "win32" else "-c"
        try:
            r = subprocess.run(["ping", param, str(count), ip], capture_output=True, timeout=5)
            if r.returncode == 0:
                results.append(ip)
        except subprocess.TimeoutExpired:
            pass
    return results
