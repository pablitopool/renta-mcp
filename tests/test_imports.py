def test_main_module_imports():
    import main  # noqa: F401


def test_helpers_package_imports():
    from helpers import env_config, logging, sentry, user_agent  # noqa: F401


def test_tools_registration_is_callable():
    from mcp.server.fastmcp import FastMCP

    from tools import register_tools

    mcp = FastMCP("renta-mcp-test")
    register_tools(mcp)


def test_resources_registration_is_callable():
    from mcp.server.fastmcp import FastMCP

    from resources import register_resources

    mcp = FastMCP("renta-mcp-test")
    register_resources(mcp)


def test_data_dir_resolves():
    from helpers.env_config import get_data_dir, get_raw_data_dir

    data_dir = get_data_dir()
    raw_dir = get_raw_data_dir()
    assert data_dir.name == "data"
    assert raw_dir.name == "raw"
    assert raw_dir.parent == data_dir
