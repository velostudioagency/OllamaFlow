from fastapi import APIRouter
from app.nodes.types import NODE_TYPES
from app.tools.definitions import TOOL_DEFINITIONS

router = APIRouter()


@router.get("/api/tools")
async def get_tools():
    tools_list = []
    details = {}
    for name, t in TOOL_DEFINITIONS.items():
        tools_list.append(name)
        details[name] = {"description": t["description"], "params": t["params"]}
    return {"tools": tools_list, "details": details}


@router.get("/api/node-types")
async def get_node_types():
    return {"node_types": NODE_TYPES}
