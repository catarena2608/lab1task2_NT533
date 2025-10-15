import requests
import base64
import time
from Identity import get_token_and_catalog, get_endpoint

def get_headers():
    token, body = get_token_and_catalog()
    return {"X-Auth-Token": token}, body

def list_instances():
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")
    resp = requests.get(f"{compute_url}/servers/detail", headers=headers)
    if resp.status_code == 200:
        servers = resp.json().get("servers", [])
        print(f"Có {len(servers)} instance:")
        for s in servers:
            print(f"- {s['name']} ({s['id']})")
        return servers
    else:
        print(f"Lỗi khi lấy danh sách instance: {resp.status_code} {resp.text}")
        return None

def list_floating_ips():
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")
    resp = requests.get(f"{network_url}/v2.0/floatingips", headers=headers)
    if resp.status_code == 200:
        floating_ips = resp.json().get("floatingips", [])
        print(f"🌐 Có {len(floating_ips)} floating IP:")
        for fip in floating_ips:
            print(f"- {fip['floating_ip_address']} (id={fip['id']})")
        return floating_ips
    else:
        print(f"❌ Lỗi khi lấy floating IP: {resp.status_code} {resp.text}")
        return None

def list_flavors():
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")
    resp = requests.get(f"{compute_url}/flavors", headers=headers)
    return resp.json().get("flavors", []) if resp.status_code == 200 else []

def list_images():
    headers, body = get_headers()
    image_url = get_endpoint(body["token"]["catalog"], "image")
    resp = requests.get(f"{image_url}/v2/images", headers=headers)
    return resp.json().get("images", []) if resp.status_code == 200 else []

def list_networks():
    headers, body = get_headers()
    network_url = get_endpoint(body["token"]["catalog"], "network")
    resp = requests.get(f"{network_url}/v2.0/networks", headers=headers)
    return resp.json().get("networks", []) if resp.status_code == 200 else []

def create_vm(name, network_name, keypair_name=None, user_data_str=None):
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")

    flavor_id = next(f["id"] for f in list_flavors() if f["name"] == "d10.xs1")
    image_id = next(i["id"] for i in list_images() if i["name"] == "CentOS 7")

    networks = list_networks()
    net = next((n for n in networks if n["name"] == network_name), None)
    if not net:
        print(f"Không tìm thấy network '{network_name}'")
        return
    network_id = net["id"]
    user_data_encoded = None
    if user_data_str:
        user_data_encoded = base64.b64encode(user_data_str.encode()).decode()

    payload = {
        "server": {
            "name": name,
            "imageRef": image_id,
            "flavorRef": flavor_id,
            "networks": [{"uuid": network_id}],
            "security_groups": [{"name": "default"}]
        }
    }
    if keypair_name: 
        payload["server"]["key_name"] = keypair_name
    if user_data_encoded: 
        payload["server"]["user_data"] = user_data_encoded

    resp = requests.post(f"{compute_url}/servers", headers=headers, json=payload)
    if resp.status_code == 202:
        data = resp.json()
        server = data.get("server")
        if not server:
            print("Không có trường 'server' trong phản hồi:", data)
            return None

        name = server.get("name", "(Không có tên)")
        id_ = server.get("id", "(Không có ID)")
        print(f"Tạo VM thành công: {name} (id={id_})")
        return server
    else:
        print(f"Lỗi tạo VM: {resp.status_code} {resp.text}")
        return None
    
def delete_instance(server_name):
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")

    # ---- Lấy danh sách servers để tìm ID từ tên ----
    servers_resp = requests.get(f"{compute_url}/servers/detail", headers=headers)
    if servers_resp.status_code != 200:
        print(f"Lỗi khi lấy danh sách servers: {servers_resp.status_code} {servers_resp.text}")
        return None

    servers = servers_resp.json().get("servers", [])
    server = next((s for s in servers if s["name"] == server_name), None)

    server_id = server["id"]

    resp = requests.delete(f"{compute_url}/servers/{server_id}", headers=headers)
    if resp.status_code == 204:
        print(f"Xóa instance '{server_name}' (id={server_id}) thành công.")
        return True
    else:
        print(f"Lỗi khi xóa instance: {resp.status_code} {resp.text}")
        return False


def attach_floating_ip(server_name, floating_ip):
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")

    servers_resp = requests.get(f"{compute_url}/servers/detail", headers=headers)
    if servers_resp.status_code != 200:
        print(f"Lỗi khi lấy danh sách servers: {servers_resp.status_code} {servers_resp.text}")
        return None

    servers = servers_resp.json().get("servers", [])
    server = next((s for s in servers if s["name"] == server_name), None)
    if not server:
        print(f"Không tìm thấy server có tên: {server_name}")
        return None

    server_id = server["id"]

    # ---- Gắn Floating IP ----
    payload = {
        "addFloatingIp": {
            "address": floating_ip
        }
    }

    resp = requests.post(f"{compute_url}/servers/{server_id}/action", headers=headers, json=payload)
    if resp.status_code == 202:
        print(f"Gắn Floating IP {floating_ip} thành công vào {server_name} (id={server_id})")
        return floating_ip
    else:
        print(f"Lỗi khi gắn Floating IP: {resp.status_code} {resp.text}")
        return None

def scale_up(base_instance_name, subnet_id, count=1):
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")

    resp = requests.get(f"{compute_url}/servers/detail", headers=headers)
    if resp.status_code != 200:
        print(f"Lỗi khi lấy danh sách servers: {resp.status_code} {resp.text}")
        return None

    servers = resp.json().get("servers", [])
    base = next((s for s in servers if s["name"] == base_instance_name), None)
    if not base:
        print(f"Không tìm thấy instance gốc '{base_instance_name}'")
        return None

    image_id = base["image"]["id"]
    flavor_id = base["flavor"]["id"]
    key_name = base.get("key_name", None)

    if not subnet_id:
        print(f"subnet_id không hợp lệ")
        return None

    created_vms = []
    for i in range(count):
        clone_name = f"{base_instance_name}-clone-{i+1}"
        payload = {
            "server": {
                "name": clone_name,
                "imageRef": image_id,
                "flavorRef": flavor_id,
                "networks": [{"uuid": subnet_id}],
                "security_groups": [{"name": "default"}]
            }
        }
        if key_name:
            payload["server"]["key_name"] = key_name

        create_resp = requests.post(f"{compute_url}/servers", headers=headers, json=payload)
        create_resp_json = create_resp.json()
        vm = create_resp_json.get("server")

        if create_resp.status_code == 202 and vm:
            # Sử dụng get() để tránh KeyError
            vm_name = vm.get("name", clone_name)
            vm_id = vm.get("id", "(chưa có ID)")
            print(f"Tạo bản sao thành công: {vm_name} (id={vm_id})")
            created_vms.append(vm_name)
        else:
            print(f"Lỗi khi tạo bản sao {clone_name}: {create_resp.status_code} {create_resp.text}")

        time.sleep(1)

    print(f"Đã scale up {len(created_vms)} VM dựa trên '{base_instance_name}'")
    return created_vms



def scale_down(base_instance_name, count=1):
    headers, body = get_headers()
    compute_url = get_endpoint(body["token"]["catalog"], "compute")

    resp = requests.get(f"{compute_url}/servers/detail", headers=headers)
    if resp.status_code != 200:
        print(f"Lỗi khi lấy danh sách servers: {resp.status_code} {resp.text}")
        return None

    servers = resp.json().get("servers", [])
    clones = [s for s in servers if s["name"].startswith(f"{base_instance_name}-clone")]

    if not clones:
        print(f"Không có bản sao nào của '{base_instance_name}' để xóa.")
        return []

    to_delete = clones[:count]
    deleted = []

    for s in to_delete:
        server_id = s["id"]
        del_resp = requests.delete(f"{compute_url}/servers/{server_id}", headers=headers)
        if del_resp.status_code == 204:
            print(f" Xóa bản sao '{s['name']}' (id={server_id}) thành công.")
            deleted.append(s["name"])
        else:
            print(f"Lỗi khi xóa '{s['name']}': {del_resp.status_code} {del_resp.text}")
        time.sleep(1)

    print(f"Đã scale down {len(deleted)} VM phụ của '{base_instance_name}'")
    return deleted