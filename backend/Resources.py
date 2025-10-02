import openstack

def get_connection(cloud="mycloud"):
    #hàm tạo connection tới OpenStack với cấu hình từ clouds.yaml đặt ở ~/.config/openstack/clouds.yaml
    return openstack.connect(cloud=cloud)

def list_vms(cloud="mycloud"):
    conn = get_connection(cloud)
    vms_info = []

    for server in conn.compute.servers():
        # Lấy trạng thái
        status = server.status

        # Lấy private IP
        private_ip = None
        floating_ip = None
        for net_name, addr_list in server.addresses.items():
            for addr in addr_list:
                if addr.get("OS-EXT-IPS:type") == "fixed":   # IP private
                    private_ip = addr["addr"]
                elif addr.get("OS-EXT-IPS:type") == "floating":  # IP public
                    floating_ip = addr["addr"]

        vms_info.append((server.name, status, private_ip, floating_ip))

    return vms_info

def create_vm(name, network_name, config_file=None, cloud="mycloud", allow_scale=False):
    conn = get_connection(cloud)

    IMAGE_NAME = "CentOS 7"
    FLAVOR_NAME = "d10.xs1"

    image = conn.compute.find_image(IMAGE_NAME)
    flavor = conn.compute.find_flavor(FLAVOR_NAME)
    network = conn.network.find_network(network_name)

    if not image or not flavor or not network:
        raise Exception("Không tìm thấy image, flavor hoặc network!")

    existing_vms = []
    for server in conn.compute.servers():
        for net_name, addresses in server.addresses.items():
            if net_name == network_name:
                existing_vms.append(server)

    if existing_vms and not allow_scale:
        raise Exception(f"Subnet '{network_name}' đã có 1 instance. Chỉ được phép scale (allow_scale=True).")

    user_data = None
    metadata = {}
    if config_file:
        with open(config_file, "r") as f:
            user_data = f.read()
        # Lưu nội dung script vào metadata để scale_up đọc lại
        metadata["user_data"] = user_data

    server = conn.compute.create_server(
        name=name,
        image_id=image.id,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
        user_data=user_data,
        metadata=metadata
    )

    server = conn.compute.wait_for_server(server)
    return server




def create_network(network_name, subnet_name, cidr, cloud="mycloud"):
    # tạo connection
    conn = get_connection(cloud)

    # tạo network
    network = conn.network.create_network(name=network_name)

    # tạo subnet trong network
    subnet = conn.network.create_subnet(
        name=subnet_name,
        network_id=network.id,
        ip_version='4',
        cidr=cidr
    )

    return network, subnet


def create_router(router_name, external_network_name, cloud="mycloud"):
    conn = get_connection(cloud)

    # tìm external network (public net)
    ext_net = conn.network.find_network(external_network_name)
    if not ext_net:
        raise Exception("Không tìm thấy external network!")

    # chỉ tạo router với external gateway
    router = conn.network.create_router(
        name=router_name,
        external_gateway_info={"network_id": ext_net.id}
    )

    return router

#hàm xóa VM theo tên
def delete_vm(name, cloud="mycloud"):
    # tạo một connection tới OpenStack
    conn = get_connection(cloud) 
    # tìm VM theo tên
    server = conn.compute.find_server(name)
    # nếu tìm thấy thì xóa VM
    if server:
        # hàm sẽ chờ đến khi VM thực sự bị xóa xong mới trả về
        conn.compute.delete_server(server, wait=True)
        return True
    return False

def delete_network(network_name, cloud="mycloud"):
    conn = get_connection(cloud)

    network = conn.network.find_network(network_name)
    if not network:
        raise Exception("Không tìm thấy network!")

    conn.network.delete_network(network, ignore_missing=False)
    return True

def delete_router(router_name, cloud="mycloud"):
    conn = get_connection(cloud)

    router = conn.network.find_router(router_name)
    if not router:
        raise Exception("Không tìm thấy router!")

    # Gỡ bỏ tất cả interface trước
    interfaces = conn.network.router_interfaces(router)
    for iface in interfaces:
        conn.network.remove_interface_from_router(router, subnet_id=iface.subnet_id)

    # Xóa router
    conn.network.delete_router(router, ignore_missing=False)
    return True

def add_interface_to_router(router_name, subnet_name, cloud="mycloud"):
    conn = get_connection(cloud)

    # tìm router
    router = conn.network.find_router(router_name)
    if not router:
        raise Exception("Không tìm thấy router!")

    # tìm subnet
    subnet = conn.network.find_subnet(subnet_name)
    if not subnet:
        raise Exception("Không tìm thấy subnet!")

    # gắn interface (subnet vào router)
    conn.network.add_interface_to_router(router, subnet_id=subnet.id)

    return True

def attach_floating_ip(server_name, external_network_name, cloud="mycloud"):
    conn = get_connection(cloud)

    # Tìm server (VM) theo tên
    server = conn.compute.find_server(server_name)
    if not server:
        raise Exception("Không tìm thấy server!")

    # Kiểm tra server đã có Floating IP chưa
    for addr_list in server.addresses.values():
        for addr in addr_list:
            if addr.get("OS-EXT-IPS:type") == "floating":
                return addr["addr"]  # VM đã có floating IP thì trả về luôn

    # Tạo hoặc lấy 1 floating IP từ external network
    fip = conn.network.create_ip(floating_network_id=conn.network.find_network(external_network_name).id)

    # Gắn floating IP vào server
    conn.compute.add_floating_ip_to_server(server, fip.floating_ip_address)

    return fip.floating_ip_address