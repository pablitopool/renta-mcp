import os
from pathlib import Path


def get_data_dir() -> Path:
    """Directorio raíz de datos fiscales (YAML curados + raw descargados).

    Respeta la variable RENTA_DATA_DIR si está definida; por defecto, apunta
    al directorio ``data/`` en la raíz del proyecto.
    """
    override = os.getenv("RENTA_DATA_DIR", "").strip()
    if override:
        return Path(override).resolve()
    return (Path(__file__).resolve().parent.parent / "data").resolve()


def get_raw_data_dir() -> Path:
    """Subdirectorio ``data/raw/`` donde viven los documentos oficiales descargados."""
    return get_data_dir() / "raw"
