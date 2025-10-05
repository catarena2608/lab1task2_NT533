from fastapi import FastAPI
from pydantic import BaseModel
import Resources
import Task

app = FastAPI(title="OpenStack VM API")

# ==== MODELS ====

class CreateVMRequest(BaseModel):
    name: str
    network_name: str
    config_file: str = None
    cloud: str = "mycloud"

class ScaleRequest(BaseModel):
    base_instance_name: str
    cloud: str = "mycloud"

class DeleteVMRequest(BaseModel):
    name: str
    cloud: str = "mycloud"

class CreateNetworkRequest(BaseModel):
    network_name: str
    subnet_name: str
    cidr: str
    cloud: str = "mycloud"

class DeleteNetworkRequest(BaseModel):
    network_name: str
    cloud: str = "mycloud"

class CreateRouterRequest(BaseModel):
    router_name: str
    external_network_name: str
    cloud: str = "mycloud"

class DeleteRouterRequest(BaseModel):
    router_name: str
    cloud: str = "mycloud"

class AddInterfaceRequest(BaseModel):
    router_name: str
    subnet_name: str
    cloud: str = "mycloud"

class AttachFloatingIPRequest(BaseModel):
    server_name: str
    external_network_name: str
    cloud: str = "mycloud"

class RemoveInterfaceRequest(BaseModel):
    router_name: str
    subnet_name: str
    cloud: str = "mycloud"


# ==== EXISTING ====

@app.get("/vms")
def get_vms(cloud: str = "mycloud"):
    return Resources.list_vms(cloud)

@app.post("/create_vm")
def api_create_vm(req: CreateVMRequest):
    server = Resources.create_vm(
        name=req.name,
        network_name=req.network_name,
        config_file=req.config_file,
        cloud=req.cloud
    )
    return {
        "id": server.id,
        "name": server.name,
        "status": server.status
    }

@app.post("/scale_up")
def api_scale_up(req: ScaleRequest):
    server = Task.scale_up(req.base_instance_name, cloud=req.cloud)
    return {
        "id": server.id,
        "name": server.name,
        "status": server.status
    }

@app.post("/scale_down")
def api_scale_down(req: ScaleRequest):
    success, deleted_vm = Task.scale_down(req.base_instance_name, cloud=req.cloud)
    return {
        "deleted_vm": deleted_vm,
        "success": success
    }

@app.post("/delete_vm")
def api_delete_vm(req: DeleteVMRequest):
    success = Resources.delete_vm(req.name, cloud=req.cloud)
    return {
        "deleted_vm": req.name,
        "success": success
    }


# ==== NEW ====

@app.post("/create_network")
def api_create_network(req: CreateNetworkRequest):
    network, subnet = Resources.create_network(
        network_name=req.network_name,
        subnet_name=req.subnet_name,
        cidr=req.cidr,
        cloud=req.cloud
    )
    return {
        "network_id": network.id,
        "network_name": network.name,
        "subnet_id": subnet.id,
        "subnet_name": subnet.name
    }

@app.post("/delete_network")
def api_delete_network(req: DeleteNetworkRequest):
    success = Resources.delete_network(req.network_name, cloud=req.cloud)
    return {
        "deleted_network": req.network_name,
        "success": success
    }

@app.post("/create_router")
def api_create_router(req: CreateRouterRequest):
    router = Resources.create_router(
        router_name=req.router_name,
        external_network_name=req.external_network_name,
        cloud=req.cloud
    )
    return {
        "router_id": router.id,
        "router_name": router.name
    }

@app.post("/delete_router")
def api_delete_router(req: DeleteRouterRequest):
    success = Resources.delete_router(req.router_name, cloud=req.cloud)
    return {
        "deleted_router": req.router_name,
        "success": success
    }

@app.post("/add_interface")
def api_add_interface(req: AddInterfaceRequest):
    success = Resources.add_interface_to_router(
        router_name=req.router_name,
        subnet_name=req.subnet_name,
        cloud=req.cloud
    )
    return {
        "router": req.router_name,
        "subnet": req.subnet_name,
        "success": success
    }

@app.post("/remove_interface")
def api_remove_interface(req: RemoveInterfaceRequest):
    success = Resources.remove_interface_from_router(
        router_name=req.router_name,
        subnet_name=req.subnet_name,
        cloud=req.cloud
    )
    return {
        "router": req.router_name,
        "subnet": req.subnet_name,
        "success": success
    }

@app.post("/attach_floating_ip")
def api_attach_floating_ip(req: AttachFloatingIPRequest):
    floating_ip = Resources.attach_floating_ip(
        server_name=req.server_name,
        external_network_name=req.external_network_name,
        cloud=req.cloud
    )
    return {
        "server": req.server_name,
        "floating_ip": floating_ip
    }