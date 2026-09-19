from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class FormatDefinition:
    name: str
    extensions: Tuple[str, ...]
    mime_types: Tuple[str, ...]
    input_type: str
    description: str


FORMAT_REGISTRY: Dict[str, FormatDefinition] = {

    "csv": FormatDefinition(
        "Comma-Separated Values",
        (".csv",),
        ("text/csv", "application/csv"),
        "CSV",
        "Tabular data and scientific measurements."
    ),

    "json": FormatDefinition(
        "JavaScript Object Notation",
        (".json",),
        ("application/json",),
        "TIME_SERIES",
        "Structured metadata or serialized measurements."
    ),

    "txt": FormatDefinition(
        "Plain Text",
        (".txt",),
        ("text/plain",),
        "TIME_SERIES",
        "Text-based scientific data or logs."
    ),

    "fits": FormatDefinition(
        "Flexible Image Transport System",
        (".fits", ".fit", ".fts"),
        ("application/fits", "image/fits"),
        "NASA",
        "Astronomical images, tables, and scientific data."
    ),

    "png": FormatDefinition(
        "Portable Network Graphics",
        (".png",),
        ("image/png",),
        "IMAGE",
        "Raster image format."
    ),

    "jpg": FormatDefinition(
        "JPEG Image",
        (".jpg", ".jpeg"),
        ("image/jpeg",),
        "IMAGE",
        "Compressed raster image format."
    ),

    "tiff": FormatDefinition(
        "Tagged Image File Format",
        (".tif", ".tiff"),
        ("image/tiff",),
        "IMAGE",
        "Raster image format for scientific imaging."
    ),

    "dicom": FormatDefinition(
        "Digital Imaging and Communications in Medicine",
        (".dcm", ".dicom"),
        ("application/dicom",),
        "DICOM",
        "Medical imaging data container."
    ),

    "mp4": FormatDefinition(
        "MPEG-4 Video",
        (".mp4",),
        ("video/mp4",),
        "VIDEO",
        "Video input format."
    ),

    "avi": FormatDefinition(
        "Audio Video Interleave",
        (".avi",),
        ("video/x-msvideo",),
        "VIDEO",
        "Video input format."
    ),

    "mov": FormatDefinition(
        "QuickTime Movie",
        (".mov",),
        ("video/quicktime",),
        "VIDEO",
        "Video input format."
    ),

    "hdf5": FormatDefinition(
        "Hierarchical Data Format 5",
        (".h5", ".hdf5"),
        ("application/x-hdf", "application/x-hdf5"),
        "TIME_SERIES",
        "Hierarchical scientific data container."
    ),

    "parquet": FormatDefinition(
        "Apache Parquet",
        (".parquet",),
        ("application/vnd.apache.parquet",),
        "TIME_SERIES",
        "Columnar data storage format."
    ),
}


EXTENSION_INDEX = {}

for definition in FORMAT_REGISTRY.values():
    for extension in definition.extensions:
        EXTENSION_INDEX[extension.lower()] = definition


MIME_INDEX = {}

for definition in FORMAT_REGISTRY.values():
    for mime_type in definition.mime_types:
        MIME_INDEX[mime_type.lower()] = definition


def normalize_extension(extension: str) -> str:

    if not isinstance(extension, str):
        raise TypeError("extension must be a string.")

    normalized = extension.strip().lower()

    if not normalized:
        return ""

    if not normalized.startswith("."):
        normalized = "." + normalized

    return normalized


def detect_by_extension(
    file_path: str
) -> Optional[FormatDefinition]:

    return EXTENSION_INDEX.get(
        Path(str(file_path)).suffix.lower()
    )


def detect_by_mime_type(
    mime_type: str
) -> Optional[FormatDefinition]:

    if not isinstance(mime_type, str):
        raise TypeError("mime_type must be a string.")

    return MIME_INDEX.get(
        mime_type.strip().lower()
    )


def detect_format(
    file_path: Optional[str] = None,
    mime_type: Optional[str] = None
) -> Dict[str, object]:

    if file_path is None and mime_type is None:
        return {
            "detected": False,
            "format_name": None,
            "input_type": "UNKNOWN",
            "extension": None,
            "mime_type": mime_type,
            "method": None,
            "message": "No file path or MIME type supplied."
        }

    definition = None
    detection_method = None
    extension = None

    if file_path is not None:

        extension = Path(
            str(file_path)
        ).suffix.lower()

        definition = EXTENSION_INDEX.get(extension)

        if definition is not None:
            detection_method = "extension"

    if definition is None and mime_type is not None:

        definition = detect_by_mime_type(mime_type)

        if definition is not None:
            detection_method = "mime_type"

    if definition is None:
        return {
            "detected": False,
            "format_name": None,
            "input_type": "UNKNOWN",
            "extension": extension,
            "mime_type": mime_type,
            "method": detection_method,
            "message": "Unknown or unsupported file format."
        }

    return {
        "detected": True,
        "format_name": definition.name,
        "input_type": definition.input_type,
        "extension": extension,
        "mime_type": mime_type,
        "method": detection_method,
        "description": definition.description
    }


def list_supported_formats() -> List[Dict[str, object]]:

    return [
        asdict(definition)
        for definition in FORMAT_REGISTRY.values()
    ]
