import Resources

def scale_up(base_instance_name, cloud="mycloud"):
    conn = Resources.get_connection(cloud)

    # Lấy VM gốc
    base_vm = conn.compute.find_server(base_instance_name)
    if not base_vm:
        raise ValueError("VM gốc không tồn tại")

    # Lấy user_data từ metadata
    user_data = base_vm.metadata.get("user_data", None)

    # Lấy network chính
    networks = list(base_vm.addresses.keys())
    if not networks:
        raise Exception("VM gốc không có network")
    network_name = networks[0]

    # Tìm các VM đã scale
    vms = Resources.list_vms(cloud)
    scale_vms = [vm for vm in vms if vm[0].startswith(base_instance_name + "-scale")]
    new_index = len(scale_vms) + 1
    new_name = f"{base_instance_name}-scale{new_index}"

    # Tạo VM mới
    server = Resources.create_vm(new_name, network_name, config_file=None, cloud=cloud, allow_scale=True)

    # Nếu VM gốc có user_data, cập nhật cho VM mới
    if user_data:
        conn.compute.update_server(server, user_data=user_data)

    return server


def scale_down(base_instance_name, cloud="mycloud"):
    """
    Xóa VM scale cuối cùng (base-scaleN)
    """
    vms = Resources.list_vms(cloud)

    # Lọc VM dạng base-scaleN, sắp xếp theo tên giảm dần
    scale_vms = sorted(
        [vm for vm in vms if vm[0].startswith(base_instance_name + "-scale")],
        key=lambda x: x[0],
        reverse=True
    )

    if not scale_vms:
        raise Exception(f"Không có VM nào để scale down cho {base_instance_name}!")

    # Lấy VM cuối cùng
    vm_to_delete = scale_vms[0][0]

    # Xóa VM
    success = Resources.delete_vm(vm_to_delete, cloud=cloud)
    return success, vm_to_delete

