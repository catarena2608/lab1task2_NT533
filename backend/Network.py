import requests
from Identity import get_token_and_catalog, get_endpoint


def get_headers():
    token, body = get_token_and_catalog()
    return {"X-Auth-Token": token}, body

def list_networks():
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")
    resp = requests.get(f"{network_url}/v2.0/networks", headers=headers)
    if resp.status_code == 200:
        networks = resp.json().get("networks", [])
        print(f"✅ Có {len(networks)} network:")
        for n in networks:
            print(f"- {n['name']} ({n['id']})")
        return networks
    else:
        print(f"❌ Lỗi khi lấy danh sách network: {resp.status_code} {resp.text}")
        return None

def create_network(name, cidr, subnet_name=None, gateway_ip=None):
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")

    # 1️⃣ Tạo network
    payload_net = {
        "network": {
            "name": name,
            "admin_state_up": True
        }
    }

    resp_net = requests.post(f"{network_url}/v2.0/networks", headers=headers, json=payload_net)
    if resp_net.status_code != 201:
        print(f"❌ Lỗi tạo network: {resp_net.status_code} {resp_net.text}")
        return None

    network = resp_net.json()["network"]
    network_id = network["id"]
    print(f"✅ Tạo network thành công: {network['name']} (id={network_id})")

    # 2️⃣ Tạo subnet trong network vừa tạo
    subnet_name = subnet_name or f"{name}_subnet"
    payload_subnet = {
        "subnet": {
            "network_id": network_id,
            "ip_version": 4,
            "cidr": cidr,
            "gateway_ip": gateway_ip,
            "name": subnet_name
        }
    }

    resp_subnet = requests.post(f"{network_url}/v2.0/subnets", headers=headers, json=payload_subnet)
    if resp_subnet.status_code == 201:
        subnet = resp_subnet.json()["subnet"]
        print(f"✅ Tạo subnet thành công: {subnet['name']} (id={subnet['id']}) CIDR={subnet['cidr']}")
    else:
        print(f"⚠️ Tạo network thành công nhưng lỗi khi tạo subnet: {resp_subnet.status_code} {resp_subnet.text}")

    return {
        "network": network,
        "subnet": resp_subnet.json().get("subnet") if resp_subnet.status_code == 201 else None
    }

# =========================================
# 🗑️ 3. Xóa Network
# =========================================
def delete_network(network_name):
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")

    networks_resp = requests.get(f"{network_url}/v2.0/networks", headers=headers)
    if networks_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy danh sách networks: {networks_resp.status_code} {networks_resp.text}")
        return None

    networks = networks_resp.json().get("networks", [])
    network = next((n for n in networks if n["name"] == network_name), None)
    if not network:
        print(f"❌ Không tìm thấy network '{network_name}'")
        return None

    network_id = network["id"]
    resp = requests.delete(f"{network_url}/v2.0/networks/{network_id}", headers=headers)
    if resp.status_code == 204:
        print(f"🗑️ Xóa network '{network_name}' (id={network_id}) thành công.")
        return True
    else:
        print(f"❌ Lỗi khi xóa network: {resp.status_code} {resp.text}")
        return False
