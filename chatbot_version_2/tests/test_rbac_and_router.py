"""Who may run which tool - the core security rules of the MCP layer."""
import pytest

from auth import rbac
from mcp_app.permissions import can_execute_mcp
from mcp_app.register_tools import TOOLS, register_all_tools
from mcp_app.registry import MCP_REGISTRY
from mcp_app.router import execute_mcp, get_available_mcps

register_all_tools()

ROLES = ["user", "admin", "super_admin"]


def test_all_18_tools_registered_and_idempotent():
    assert len(MCP_REGISTRY) == len(TOOLS) == 18
    assert register_all_tools() == 18          # second call must not crash


@pytest.mark.parametrize("name,handler,desc,tool_role,permission", TOOLS)
def test_every_tool_is_allowed_only_for_its_own_role(name, handler, desc, tool_role, permission):
    for role in ROLES:
        expected = role == tool_role
        assert can_execute_mcp(role, name, permission) is expected, (name, role)


@pytest.mark.parametrize("name,handler,desc,tool_role,permission", TOOLS)
def test_every_tool_permission_exists_in_rbac_table(name, handler, desc, tool_role, permission):
    assert rbac.has_permission(tool_role, permission), f"{name}: {permission} missing in rbac"


def test_rbac_table_is_enforced_not_just_role_names(monkeypatch):
    """If RBAC revokes a permission, the tool must stop working."""
    monkeypatch.setattr(rbac, "ROLE_PERMISSIONS", {**rbac.ROLE_PERMISSIONS, "user": set()})
    assert can_execute_mcp("user", "get_doctors", "doctor.read") is False


def test_role_cannot_run_another_roles_tool():
    r = execute_mcp("search_patients", {"id": 1, "role": "user"}, {})
    assert r["success"] is False and "not authorized" in r["error"]
    r = execute_mcp("get_doctors", {"id": 1, "role": "admin"}, {})
    assert r["success"] is False
    r = execute_mcp("search_patients", {"id": 1, "role": "super_admin"}, {})
    assert r["success"] is False


def test_unknown_tool_and_bad_identity():
    assert execute_mcp("does_not_exist", {"id": 1, "role": "user"}, {})["error"] == "MCP not found."
    assert execute_mcp("get_doctors", {"id": 1, "role": "hacker"}, {})["success"] is False
    assert execute_mcp("get_doctors", None, {})["success"] is False
    assert execute_mcp("get_doctors", {"role": "user"}, {})["success"] is False  # no id


def test_identity_fields_cannot_be_smuggled_in_arguments():
    r = execute_mcp("get_doctors", {"id": 1, "role": "user"}, {"role": "admin"})
    assert r["success"] is False and "Identity" in r["error"]


def test_tools_offered_per_role():
    assert len(get_available_mcps("user")) == 10
    assert len(get_available_mcps("admin")) == 5
    assert len(get_available_mcps("super_admin")) == 3
    assert get_available_mcps("nobody") == []
    names_user = {m["name"] for m in get_available_mcps("user")}
    assert "search_patients" not in names_user


def test_tool_exception_is_contained(monkeypatch):
    def boom(**kw):
        raise RuntimeError("sql exploded")
    monkeypatch.setitem(MCP_REGISTRY["get_doctors"], "handler", boom)
    r = execute_mcp("get_doctors", {"id": 1, "role": "user"}, {})
    assert r == {"success": False, "error": "MCP execution failed."}


def test_stdio_server_handlers_are_locked():
    """The directly exposed MCP server must refuse every call."""
    import asyncio
    from mcp_app.server import mcp_server

    async def run():
        tools = await mcp_server.list_tools()
        assert len(tools) == 18
        with pytest.raises(Exception):
            await mcp_server.call_tool("get_doctors", {})
    asyncio.run(run())


def test_registering_twice_through_two_module_names_does_not_crash():
    """
    The website's root main.py may import  chatbot_version_2.mcp_app.register_tools
    while llm/agent.py imports  mcp_app.register_tools  -> two copies of the
    module, one shared registry. Both must be able to call register_all_tools().
    """
    import importlib.util
    import mcp_app.register_tools as first

    spec = importlib.util.spec_from_file_location("second_copy_of_register_tools", first.__file__)
    second = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(second)

    assert first is not second
    assert first.register_all_tools() == 18
    assert second.register_all_tools() == 18
    assert len(MCP_REGISTRY) == 18
