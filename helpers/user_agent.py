from importlib.metadata import PackageNotFoundError, version

try:
    _VERSION = version("renta-mcp")
except PackageNotFoundError:
    _VERSION = "dev"

USER_AGENT = (
    f"renta-mcp/{_VERSION} "
    "(+https://github.com/pablitopool/renta-mcp; contacto@pmgallardodev.com)"
)
