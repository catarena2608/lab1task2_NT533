import Resources

print("Danh sách VM hiện có:")
for vm in Resources.list_vms():
    print(vm)

# Ví dụ tạo VM
# new_vm = Resources.create_vm("test-vm", "Centos7", "m1.small", "private-net")
# print("Đã tạo VM:", new_vm.name, new_vm.status)

# Ví dụ xóa VM
# vm_manager.delete_vm("test-vm")
# print("VM test-vm đã bị xóa")
