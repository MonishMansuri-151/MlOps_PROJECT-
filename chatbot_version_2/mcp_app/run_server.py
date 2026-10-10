from mcp_app.server import mcp_server
from mcp_app.register_tools import register_all_tools
from src.logger import get_logger 
logger = get_logger(__name__)

def main():
    registered_count = register_all_tools()
    logger.info("Registered %s Sanjivni MCP tools.", registered_count)

    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()