def build_map(hosts):
    gateways = [h for h in hosts if is_gateway(h)]
    nodes = [h for h in hosts if not is_gateway(h)]
    connections = []
    for gw in gateways:
        for node in nodes:
            connections.append({"from": gw["ip"], "to": node["ip"]})
    return {"gateways": gateways, "nodes": nodes, "connections": connections}

def is_gateway(host):
    ip = host.get("ip", "")
    return ip.endswith(".1") or ip.endswith(".254")
