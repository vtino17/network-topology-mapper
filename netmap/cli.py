import argparse
import sys
from netmap.discovery import arp_scan
from netmap.topology import build_map
from netmap.reporter import generate_html


def entry_point():
    parser = argparse.ArgumentParser(description="Network Topology Mapper")
    parser.add_argument("--subnet", "-s", default="192.168.1.0/24")
    parser.add_argument("--output", "-o", default="topology.html")
    args = parser.parse_args()

    hosts = arp_scan(args.subnet)
    html = generate_html(hosts)
    with open(args.output, "w") as f:
        f.write(html)
    print(f"Report: {args.output} ({len(hosts)} hosts)")


if __name__ == "__main__":
    entry_point()
