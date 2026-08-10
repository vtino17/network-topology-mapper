from unittest.mock import patch

import pytest

from netmap.discovery import ARP_ENTRY, arp_scan, parse_arp_output, ping_sweep
from netmap.topology import build_map, is_gateway


LINUX = """\
? (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on wlan0
? (192.168.1.5) at <incomplete> on wlan0
? (192.168.1.20) at 11:22:33:44:55:66 [ether] on wlan0
"""

BSD = """\
router (192.168.1.1) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
printer (192.168.1.20) at 11:22:33:44:55:66 on en0 ifscope [ethernet]
"""

WINDOWS = """\
Interface: 192.168.1.10 --- 0x5
  Internet Address      Physical Address      Type
  192.168.1.1           aa-bb-cc-dd-ee-ff     dynamic
  192.168.1.20          11-22-33-44-55-66     dynamic
"""


@pytest.fixture(autouse=True)
def no_reverse_dns():
    with patch("netmap.discovery.resolve_hostname", return_value=None):
        yield


class TestArpParsing:

    @pytest.mark.parametrize("name,output", [
        ("linux", LINUX), ("bsd", BSD), ("windows", WINDOWS),
    ])
    def test_every_platform_format_is_parsed(self, name, output):
        hosts = parse_arp_output(output)
        assert [h["ip"] for h in hosts] == ["192.168.1.1", "192.168.1.20"]

    @pytest.mark.parametrize("output", [LINUX, BSD, WINDOWS])
    def test_macs_are_normalised_to_lowercase_colons(self, output):
        assert parse_arp_output(output)[0]["mac"] == "aa:bb:cc:dd:ee:ff"

    def test_incomplete_entries_are_skipped(self):
        assert all(h["ip"] != "192.168.1.5" for h in parse_arp_output(LINUX))

    def test_headers_are_not_mistaken_for_entries(self):
        # "Interface: 192.168.1.10 --- 0x5" carries an address but no MAC.
        assert all(h["ip"] != "192.168.1.10" for h in parse_arp_output(WINDOWS))

    def test_empty_output(self):
        assert parse_arp_output("") == []

    def test_uppercase_mac_is_accepted(self):
        line = "? (10.0.0.2) at AA:BB:CC:DD:EE:FF [ether] on eth0"
        assert parse_arp_output(line)[0]["mac"] == "aa:bb:cc:dd:ee:ff"

    def test_pattern_requires_six_octets(self):
        assert ARP_ENTRY.search("? (10.0.0.2) at aa:bb:cc:dd:ee [ether] on eth0") is None


class TestSubnetFilter:

    def test_entries_outside_the_subnet_are_dropped(self):
        assert parse_arp_output(LINUX, "10.0.0.0/24") == []

    def test_entries_inside_the_subnet_are_kept(self):
        assert len(parse_arp_output(LINUX, "192.168.1.0/24")) == 2

    def test_subnet_without_a_prefix_length(self):
        assert len(parse_arp_output(LINUX, "192.168.1.0")) == 2

    def test_no_subnet_returns_everything(self):
        assert len(parse_arp_output(LINUX, None)) == 2


class TestArpScan:

    def test_missing_arp_binary_returns_empty(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert arp_scan("192.168.1.0/24") == []

    def test_timeout_returns_empty(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("arp", 10)):
            assert arp_scan("192.168.1.0/24") == []

    def test_output_is_passed_through_the_parser(self):
        completed = type("R", (), {"stdout": LINUX})()
        with patch("subprocess.run", return_value=completed):
            hosts = arp_scan("192.168.1.0/24")
        assert [h["ip"] for h in hosts] == ["192.168.1.1", "192.168.1.20"]


class TestPingSweep:

    def test_sweep_runs_without_raising(self):
        # Previously NameError: name 'sys' is not defined on the first call.
        completed = type("R", (), {"returncode": 1})()
        with patch("subprocess.run", return_value=completed):
            assert ping_sweep("192.168.1.0/24") == []

    def test_responding_hosts_are_collected(self):
        completed = type("R", (), {"returncode": 0})()
        with patch("subprocess.run", return_value=completed):
            alive = ping_sweep("192.168.1.0/24")
        assert alive[0] == "192.168.1.1"
        assert len(alive) == 254

    def test_prefix_length_controls_scan_scope(self):
        completed = type("R", (), {"returncode": 0})()
        with patch("subprocess.run", return_value=completed) as run:
            alive = ping_sweep("192.0.2.0/30")
        assert alive == ["192.0.2.1", "192.0.2.2"]
        assert run.call_count == 2

    def test_oversized_network_is_rejected_before_execution(self):
        with patch("subprocess.run") as run, pytest.raises(ValueError, match="maximum"):
            ping_sweep("10.0.0.0/8")
        run.assert_not_called()


class TestTopology:

    def test_gateway_detection(self):
        assert is_gateway({"ip": "192.168.1.1"})
        assert is_gateway({"ip": "192.168.1.254"})
        assert not is_gateway({"ip": "192.168.1.20"})

    def test_missing_ip_is_not_a_gateway(self):
        assert not is_gateway({})

    def test_map_links_every_gateway_to_every_node(self):
        hosts = [{"ip": "192.168.1.1"}, {"ip": "192.168.1.20"}, {"ip": "192.168.1.21"}]
        result = build_map(hosts)
        assert len(result["gateways"]) == 1
        assert len(result["nodes"]) == 2
        assert len(result["connections"]) == 2

    def test_map_with_no_gateway_has_no_connections(self):
        result = build_map([{"ip": "192.168.1.20"}])
        assert result["connections"] == []
