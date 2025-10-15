from fastapi import FastAPI
from pydantic import BaseModel
import Instance
import Network
import Router
import LoadBalancer

app = FastAPI(title="OpenStack VM API")

# ==== MODELS ====

class CreateVMRequest(BaseModel):
    name: str
    network_name: str
    key_name: str | None = None
    user_data: str | None = None

class ScaleRequest(BaseModel):
    base_instance_name: str
    subnet_id: str
    count: int = 1

class DeleteVMRequest(BaseModel):
    name: str

class CreateNetworkRequest(BaseModel):
    name: str
    cidr: str
    subnet_name: str | None = None
    gateway_ip: str | None = None

class DeleteNetworkRequest(BaseModel):
    name: str

class CreateRouterRequest(BaseModel):
    router_name: str
    external_network_name: str

class DeleteRouterRequest(BaseModel):
    router_name: str

class AddInterfaceRequest(BaseModel):
    router_name: str
    subnet_name: str

class RemoveInterfaceRequest(BaseModel):
    router_name: str
    subnet_name: str

class AttachFloatingIPRequest(BaseModel):
    server_name: str
    floating_ip: str

class CreateLBRequest(BaseModel):
    name: str
    vip_subnet_id: str
    description: str | None = None

class CreateListenerRequest(BaseModel):
    name: str
    lb_name: str
    protocol: str | None = "HTTP"
    protocol_port: int | None = 80

class CreatePoolRequest(BaseModel):
    name: str
    lb_name: str
    protocol: str | None = "HTTP"
    lb_algorithm: str | None = "ROUND_ROBIN"

class DeleteLBRequest(BaseModel):
    name: str



# ==== EXISTING ====

@app.get("/vms")
def get_vms():
    return Instance.list_instances()

@app.get("/networks")
def get_networks():
    return Network.list_networks    ()

@app.post("/create_vm")
def api_create_vm(req: CreateVMRequest):
    server = Instance.create_vm(
        name=req.name,
        network_name=req.network_name,
        keypair_name=req.key_name,
        user_data_str=req.user_data
    )
    return {
        "id": server.get("id"),
        "name": server.get("name"),
        "status": server.get("status", "BUILD")
    }

@app.post("/scale_up")
def api_scale_up(req: ScaleRequest):
    created_vms = Instance.scale_up(
        base_instance_name = req.base_instance_name,
        subnet_id = req.subnet_id,
    )
    return {
        "success": True,
        "base_instance": req.base_instance_name,
        "created_clones": created_vms,
        "count": len(created_vms)
    }

@app.post("/scale_down")
def api_scale_down(req: ScaleRequest):
    deleted_vms = Instance.scale_down(req.base_instance_name)
    return {
        "success": True,
        "base_instance": req.base_instance_name,
        "deleted_clones": deleted_vms,
        "count": len(deleted_vms)
    }

@app.post("/delete_vm")
def api_delete_vm(req: DeleteVMRequest):
    success = Instance.delete_instance(req.name)
    return {
        "deleted_vm": req.name,
        "success": success
    }

@app.post("/create_network")
def api_create_network(req: CreateNetworkRequest):
    result = Network.create_network(
        name=req.name,
        cidr=req.cidr,
        subnet_name=req.subnet_name,
        gateway_ip=req.gateway_ip
    )
    network = result.get("network")
    subnet = result.get("subnet")
    return {
        "network_id": network.get("id") if network else None,
        "network_name": network.get("name") if network else None,
        "subnet_id": subnet.get("id") if subnet else None,
        "subnet_name": subnet.get("name") if subnet else None,
    }

@app.post("/delete_network")
def api_delete_network(req: DeleteNetworkRequest):
    success = Network.delete_network(req.name)
    return {
        "deleted_network": req.name,
        "success": success
    }

@app.post("/create_router")
def api_create_router(req: CreateRouterRequest):
    router = Router.create_router(
        router_name=req.router_name,
        external_network_name=req.external_network_name
    )
    return {
            "router_id": router.get("id"),
            "router_name": router.get("name"),  
            "status": "created"
    }
    

@app.post("/delete_router")
def api_delete_router(req: DeleteRouterRequest):
    success = Router.delete_router(req.router_name)
    return {
        "deleted_router": req.router_name,
        "success": success
    }

@app.post("/add_interface")
def api_add_interface(req: AddInterfaceRequest):
    success = Router.add_interface(
        router_name=req.router_name,
        subnet_name=req.subnet_name
    )
    return {
        "router": req.router_name,
        "subnet": req.subnet_name,
        "success": success
    }

@app.post("/remove_interface")
def api_remove_interface(req: RemoveInterfaceRequest):
    success = Router.remove_interface(
        router_name=req.router_name,
        subnet_name=req.subnet_name
    )
    return {
        "router": req.router_name,
        "subnet": req.subnet_name,
        "success": success
    }

@app.post("/attach_floating_ip")
def api_attach_floating_ip(req: AttachFloatingIPRequest):
    floating_ip = Instance.attach_floating_ip(
        server_name=req.server_name,
        floating_ip=req.floating_ip
    )
    return {
        "server": req.server_name,
        "floating_ip": floating_ip
    }

@app.post("/create_lb")
def api_create_lb(req: CreateLBRequest):
    lb = LoadBalancer.create_lb(
        name=req.name,
        vip_subnet_id= req.vip_subnet_id,
        description=req.description
    )
    return {
        "lb_id": lb.get("id"),
        "lb_name": lb.get("name"),
        "status": "created"
    }

@app.post("/create_listener")
def api_create_listener(req: CreateListenerRequest):
    listener = LoadBalancer.create_listener(
        name=req.name,
        lb_name=req.lb_name,
        protocol=req.protocol,
        protocol_port=req.protocol_port
    )
    return {
        "listener_id": listener.get("id"),
        "listener_name": listener.get("name"),
        "lb_name": req.lb_name,
        "status": "created"
    }

@app.post("/create_pool")
def api_create_pool(req: CreatePoolRequest):
    pool = LoadBalancer.create_pool(
        name=req.name,
        lb_name=req.lb_name,
        protocol=req.protocol,
        lb_algorithm=req.lb_algorithm
    )
    return {
        "pool_id": pool.get("id"),
        "pool_name": pool.get("name"),
        "lb_name": req.lb_name
    }

@app.post("/delete_lb")
def api_delete_lb(req: DeleteLBRequest):
    success = LoadBalancer.delete_lb(req.name)
    return {
        "lb_name": req.name,
        "success": success
    }