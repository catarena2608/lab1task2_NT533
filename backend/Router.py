import requests
from Identity import get_token_and_catalog, get_endpoint


def get_headers():
    token, body = get_token_and_catalog()
    return {"X-Auth-Token": token}, body


def create_router(router_name, external_network_name):
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")

    # Lấy danh sách network để tìm external_network_id
    resp_nets = requests.get(f"{network_url}/v2.0/networks", headers=headers)
    if resp_nets.status_code != 200:
        print(f"❌ Lỗi khi lấy danh sách network: {resp_nets.status_code} {resp_nets.text}")
        return None

    networks = resp_nets.json().get("networks", [])
    external_net = next((n for n in networks if n["name"] == external_network_name), None)
    if not external_net:
        print(f"❌ Không tìm thấy external network '{external_network_name}'")
        return None

    payload = {
        "router": {
            "name": router_name,
            "admin_state_up": True,
            "external_gateway_info": {
                "network_id": external_net["id"]
            }
        }
    }

    resp = requests.post(f"{network_url}/v2.0/routers", headers=headers, json=payload)
    if resp.status_code == 201:
        router = resp.json()["router"]
        print(f"✅ Tạo router thành công: {router['name']} (id={router['id']})")
        return router
    else:
        print(f"❌ Lỗi tạo router: {resp.status_code} {resp.text}")
        return None

def delete_router(router_name):
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")

    # Lấy danh sách router để tìm ID
    routers_resp = requests.get(f"{network_url}/v2.0/routers", headers=headers)
    if routers_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy danh sách router: {routers_resp.status_code} {routers_resp.text}")
        return None

    routers = routers_resp.json().get("routers", [])
    router = next((r for r in routers if r["name"] == router_name), None)
    if not router:
        print(f"❌ Không tìm thấy router '{router_name}'")
        return None

    router_id = router["id"]
    resp = requests.delete(f"{network_url}/v2.0/routers/{router_id}", headers=headers)
    if resp.status_code == 204:
        print(f"🗑️ Xóa router '{router_name}' (id={router_id}) thành công.")
        return True
    else:
        print(f"❌ Lỗi khi xóa router: {resp.status_code} {resp.text}")
        return False

def add_interface(router_name, subnet_name):
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")

    # Lấy ID router
    routers_resp = requests.get(f"{network_url}/v2.0/routers", headers=headers)
    if routers_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy router: {routers_resp.status_code} {routers_resp.text}")
        return False
    routers = routers_resp.json().get("routers", [])
    router = next((r for r in routers if r["name"] == router_name), None)
    if not router:
        print(f"❌ Không tìm thấy router '{router_name}'")
        return False
    router_id = router["id"]

    # Lấy ID subnet
    subnets_resp = requests.get(f"{network_url}/v2.0/subnets", headers=headers)
    if subnets_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy subnet: {subnets_resp.status_code} {subnets_resp.text}")
        return False
    subnets = subnets_resp.json().get("subnets", [])
    subnet = next((s for s in subnets if s["name"] == subnet_name), None)
    if not subnet:
        print(f"❌ Không tìm thấy subnet '{subnet_name}'")
        return False
    subnet_id = subnet["id"]

    payload = {"subnet_id": subnet_id}
    resp = requests.put(f"{network_url}/v2.0/routers/{router_id}/add_router_interface", headers=headers, json=payload)
    if resp.status_code == 200:
        print(f"🔗 Thêm subnet '{subnet_name}' vào router '{router_name}' thành công.")
        return True
    else:
        print(f"❌ Lỗi thêm interface: {resp.status_code} {resp.text}")
        return False


# =========================================
# ❎ 4. Gỡ Interface
# =========================================
def remove_interface(router_name, subnet_name):
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")

    # Lấy ID router
    routers_resp = requests.get(f"{network_url}/v2.0/routers", headers=headers)
    if routers_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy router: {routers_resp.status_code} {routers_resp.text}")
        return False
    routers = routers_resp.json().get("routers", [])
    router = next((r for r in routers if r["name"] == router_name), None)
    if not router:
        print(f"❌ Không tìm thấy router '{router_name}'")
        return False
    router_id = router["id"]

    # Lấy ID subnet
    subnets_resp = requests.get(f"{network_url}/v2.0/subnets", headers=headers)
    if subnets_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy subnet: {subnets_resp.status_code} {subnets_resp.text}")
        return False
    subnets = subnets_resp.json().get("subnets", [])
    subnet = next((s for s in subnets if s["name"] == subnet_name), None)
    if not subnet:
        print(f"❌ Không tìm thấy subnet '{subnet_name}'")
        return False
    subnet_id = subnet["id"]

    payload = {"subnet_id": subnet_id}
    resp = requests.put(f"{network_url}/v2.0/routers/{router_id}/remove_router_interface", headers=headers, json=payload)
    if resp.status_code == 200:
        print(f"❎ Gỡ subnet '{subnet_name}' khỏi router '{router_name}' thành công.")
        return True
    else:
        print(f"❌ Lỗi gỡ interface: {resp.status_code} {resp.text}")
        return False
