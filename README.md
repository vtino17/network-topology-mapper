# Network Topology Mapper

[![CI](https://github.com/vtino17/network-topology-mapper/actions/workflows/ci.yml/badge.svg)](https://github.com/vtino17/network-topology-mapper/actions/workflows/ci.yml)

ARP-based network discovery tool. Discovers live hosts, resolves MAC vendors, builds network maps, and generates HTML topology reports.

## Quick Start

```bash
pip install -e .
python -m netmap.cli
```

### Options

```bash
python -m netmap.cli --target 192.168.1.0/24 --output report.html
```

## Features

- ARP-based host discovery
- MAC address vendor resolution
- Network topology mapping
- HTML report generation

## License

MIT
