import requests
import time
from Identity import get_token_and_catalog, get_endpoint
import Network

def get_headers():
    token, body = get_token_and_catalog()
    return {"X-Auth-Token": token}, body


def create_lb(name, vip_subnet_id, description=None):
    headers, body = get_headers()
    lb_url = get_endpoint(body["token"]["catalog"], "load-balancer")

    if not vip_subnet_id:
        print("❌ Không có subnet_id hợp lệ")
        return None

    payload = {
        "loadbalancer": {
            "name": name,
            "vip_subnet_id": vip_subnet_id,
            "description": description or "",
            "admin_state_up": True
        }
    }

    resp = requests.post(f"{lb_url}/v2.0/lbaas/loadbalancers", headers=headers, json=payload)
    if resp.status_code == 201:
        lb = resp.json()["loadbalancer"]
        print(f"✅ Tạo Load Balancer thành công: {lb['name']} (id={lb['id']})")
        return lb
    else:
        print(f"❌ Lỗi tạo Load Balancer: {resp.status_code} {resp.text}")
        return None

def create_listener(name, lb_name, protocol="HTTP", protocol_port=80):
    headers, body = get_headers()
    lb_url = get_endpoint(body["token"]["catalog"], "load-balancer")

    # Lấy id từ tên Load Balancer
    lbs_resp = requests.get(f"{lb_url}/v2.0/lbaas/loadbalancers", headers=headers)
    if lbs_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy danh sách Load Balancer: {lbs_resp.status_code} {lbs_resp.text}")
        return None

    lbs = lbs_resp.json().get("loadbalancers", [])
    lb = next((l for l in lbs if l["name"] == lb_name), None)
    if not lb:
        print(f"❌ Không tìm thấy Load Balancer '{lb_name}'")
        return None

    lb_id = lb["id"]

    payload = {
        "listener": {
            "name": name,
            "loadbalancer_id": lb_id,
            "protocol": protocol,
            "protocol_port": protocol_port,
            "admin_state_up": True
        }
    }

    resp = requests.post(f"{lb_url}/v2.0/lbaas/listeners", headers=headers, json=payload)
    if resp.status_code == 201:
        listener = resp.json()["listener"]
        print(f"✅ Tạo Listener thành công: {listener['name']} (id={listener['id']}) trên LB {lb_name}")
        return listener
    else:
        print(f"❌ Lỗi tạo Listener: {resp.status_code} {resp.text}")
        return None


def create_pool(name, lb_name, protocol="HTTP", lb_algorithm="ROUND_ROBIN"):
    headers, body = get_headers()
    lb_url = get_endpoint(body["token"]["catalog"], "load-balancer")

    # Lấy id từ tên Load Balancer
    lbs_resp = requests.get(f"{lb_url}/v2.0/lbaas/loadbalancers", headers=headers)
    if lbs_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy danh sách Load Balancer: {lbs_resp.status_code} {lbs_resp.text}")
        return None

    lbs = lbs_resp.json().get("loadbalancers", [])
    lb = next((l for l in lbs if l["name"] == lb_name), None)
    if not lb:
        print(f"❌ Không tìm thấy Load Balancer '{lb_name}'")
        return None

    lb_id = lb["id"]

    payload = {
        "pool": {
            "name": name,
            "loadbalancer_id": lb_id,
            "protocol": protocol,
            "lb_algorithm": lb_algorithm,
            "admin_state_up": True
        }
    }

    resp = requests.post(f"{lb_url}/v2.0/lbaas/pools", headers=headers, json=payload)
    if resp.status_code == 201:
        pool = resp.json()["pool"]
        print(f"✅ Tạo Pool thành công: {pool['name']} (id={pool['id']})")
        return pool
    else:
        print(f"❌ Lỗi tạo Pool: {resp.status_code} {resp.text}")
        return None


def delete_lb(lb_name):
    headers, body = get_headers()
    lb_url = get_endpoint(body["token"]["catalog"], "load-balancer")

    # Lấy danh sách LB
    lbs_resp = requests.get(f"{lb_url}/v2.0/lbaas/loadbalancers", headers=headers)
    if lbs_resp.status_code != 200:
        print(f"❌ Lỗi khi lấy danh sách LB: {lbs_resp.status_code}")
        return False

    lbs = lbs_resp.json().get("loadbalancers", [])
    lb = next((l for l in lbs if l["name"] == lb_name), None)
    if not lb:
        print(f"⚠️ Không tìm thấy LB '{lb_name}'")
        return False

    lb_id = lb["id"]

    # Xóa tất cả listeners
    listeners_resp = requests.get(f"{lb_url}/v2.0/lbaas/listeners", headers=headers)
    if listeners_resp.status_code == 200:
        for listener in [l for l in listeners_resp.json().get("listeners", []) if l["loadbalancer_id"] == lb_id]:
            requests.delete(f"{lb_url}/v2.0/lbaas/listeners/{listener['id']}", headers=headers)
            print(f"🗑️ Đã xóa Listener {listener['name']}")

    # Xóa tất cả pools
    pools_resp = requests.get(f"{lb_url}/v2.0/lbaas/pools", headers=headers)
    if pools_resp.status_code == 200:
        for pool in [p for p in pools_resp.json().get("pools", []) if p["loadbalancer_id"] == lb_id]:
            requests.delete(f"{lb_url}/v2.0/lbaas/pools/{pool['id']}", headers=headers)
            print(f"🗑️ Đã xóa Pool {pool['name']}")

    # Xóa LB
    del_resp = requests.delete(f"{lb_url}/v2.0/lbaas/loadbalancers/{lb_id}", headers=headers)
    if del_resp.status_code not in [200, 202, 204]:
        print(f"❌ Lỗi xóa LB: {del_resp.status_code} {del_resp.text}")
        return False

    # Polling chờ LB thực sự bị xóa
    for _ in range(10):
        time.sleep(2)
        check_resp = requests.get(f"{lb_url}/v2.0/lbaas/loadbalancers/{lb_id}", headers=headers)
        if check_resp.status_code == 404:
            print(f"✅ LB '{lb_name}' đã xóa thành công")
            return True

    print(f"⚠️ LB '{lb_name}' chưa xóa xong, hãy thử lại sau")
    return False
