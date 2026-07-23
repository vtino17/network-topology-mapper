def generate_html(hosts):
    rows = ""
    for h in hosts:
        ip = h.get("ip", "")
        mac = h.get("mac", "")
        hostname = h.get("hostname", "") or ""
        rows += f"<tr><td>{ip}</td><td>{hostname}</td><td>{mac}</td></tr>"
    return f"""<!DOCTYPE html><html><head><title>Network Topology</title>
<style>body{{font-family:Arial;background:#0d1117;color:#c9d1d9;margin:20px}}
h1{{color:#58a6ff}}table{{width:100%;border-collapse:collapse}}
th{{background:#161b22;padding:10px;text-align:left;color:#8b949e}}
td{{padding:8px;border-bottom:1px solid #30363d}}
.count{{font-size:14px;color:#8b949e}}</style></head><body>
<h1>Network Topology</h1>
<p class='count'>Discovered {len(hosts)} hosts</p>
<table><thead><tr><th>IP</th><th>Hostname</th><th>MAC</th></tr></thead>
<tbody>{rows}</tbody></table></body></html>"""
