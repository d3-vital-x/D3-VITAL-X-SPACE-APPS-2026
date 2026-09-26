# ============================================================
# D³ VITAL-X SPACE INTELLIGENCE PLATFORM
# Module 57 — app.py
# Functional Streamlit Dashboard Entry Point
#
# Public framework only.
# Proprietary intelligence core is NOT included.
# ============================================================

from pathlib import Path
import sys
import io
import hashlib
import json
from datetime import datetime, timezone
import numpy as np
import streamlit as st

# ============================================================
# PROJECT PATH & 06_ANALYTICS FOLDER INTEGRATION
# ============================================================
CURRENT_DIR = Path(__file__).parent.resolve()
ANALYTICS_PATH = CURRENT_DIR / "06_ANALYTICS"

# 06_ANALYTICS ফোল্ডারটিকে Python Path-এ যুক্ত করা
if ANALYTICS_PATH.exists() and str(ANALYTICS_PATH) not in sys.path:
    sys.path.insert(0, str(ANALYTICS_PATH))

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# ============================================================
# DYNAMIC IMPORTS FOR MODULES 18 TO 22 (FROM 06_ANALYTICS)
# ============================================================
ANALYTICS_AVAILABLE = False

try:
    from metrics import (
        create_standard_metric_registry,
        create_metric,
        create_metric_set,
        summarize_metric_set,
    )
    from transition_analysis import analyze_transition_1d, analyze_transition_2d
    from anomaly_scoring import calculate_anomaly_score_1d, calculate_anomaly_score_2d
    from uncertainty import evaluate_uncertainty_bounds
    from explainability import generate_explainability_report
    ANALYTICS_AVAILABLE = True
except Exception as e:
    ANALYTICS_AVAILABLE = False

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="D³ VITAL-X Space Intelligence Platform",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CONSTANTS
# ============================================================
APP_VERSION = "0.1.0-development"
SUPPORTED_PUBLIC_INPUTS = [
    "CSV",
    "Image",
    "Time-Series",
]
PROJECT_STATUS = "ACTIVE DEVELOPMENT"

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def utc_timestamp():
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()

def calculate_sha256(data: bytes) -> str:
    """Calculate SHA-256 hash of raw uploaded bytes."""
    return hashlib.sha256(data).hexdigest()

def format_bytes(size):
    """Human-readable file size."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    if size < 1024 ** 3:
        return f"{size / 1024 ** 2:.2f} MB"
    return f"{size / 1024 ** 3:.2f} GB"

def detect_input_type(filename):
    """Detect supported public input type from filename."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return "CSV"
    if suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"]:
        return "IMAGE"
    if suffix in [".txt", ".dat"]:
        return "TIME-SERIES"
    return "UNKNOWN"

# ============================================================
# HEADER
# ============================================================
st.title("🛰️ D³ VITAL-X Space Intelligence Platform")
st.markdown(
    """
    ### One AI Engine. Multiple Worlds. One Signal Language.
    **Independent research prototype — D³ VITAL-X BANGLADESH**

    This dashboard provides a public interface for scientific data ingestion, technical quality assessment, exploratory analysis, and visualization.

    > **Development Status: ACTIVE DEVELOPMENT**
    """
)

# ============================================================
# PROJECT STATUS BANNER
# ============================================================
st.info(
    "🔬 This is a work-in-progress research prototype. "
    "Some analytics, NASA integration, biomedical workflows, "
    "live mode, and advanced visualization modules are under development."
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("🛰️ D³ VITAL-X")
    st.caption(f"Version: {APP_VERSION}")
    st.divider()
    st.subheader("Navigation")
    page = st.radio(
        "Select Mode",
        [
            "🏠 Home",
            "📥 Data Upload",
            "🔬 Data Quality",
            "📊 Visualization",
            "🛰️ Space Mode",
            "🩻 Biomedical Mode",
            "🎥 Live Mode",
            "ℹ️ About",
        ],
    )
    st.divider()
    st.subheader("System Status")
    st.success("Public Framework: Available")
    st.success("Input Layer: Available")
    st.success("Unified Data Layer: Available")
    
    if ANALYTICS_AVAILABLE:
        st.success("Advanced Analytics (18–22): Connected")
    else:
        st.warning("Advanced Analytics: Under Development")
        
    st.warning("NASA Integration: Under Development")
    st.warning("Live Mode: Under Development")
    st.divider()
    st.caption("D³ VITAL-X BANGLADESH")

# ============================================================
# SESSION STATE
# ============================================================
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None
if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = None
if "uploaded_type" not in st.session_state:
    st.session_state.uploaded_type = None
if "uploaded_hash" not in st.session_state:
    st.session_state.uploaded_hash = None
if "uploaded_size" not in st.session_state:
    st.session_state.uploaded_size = None
if "analytics_results" not in st.session_state:
    st.session_state.analytics_results = None

# ============================================================
# HOME
# ============================================================
if page == "🏠 Home":
    st.header("Welcome to D³ VITAL-X")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Input Modes", "3")
    with col2:
        st.metric("Data Layer", "Active")
    with col3:
        st.metric("QC Framework", "Active")
    with col4:
        st.metric("Development", "Ongoing")

    st.divider()
    st.subheader("Current Public Architecture")
    architecture = [
        "Input Adapters",
        "Unified Data Layer",
        "Data Validation",
        "Quality Control",
        "Feature Engine Interface",
        "Analytics (Modules 18–22 Integrated)",
        "Visualization",
        "Dashboard",
    ]
    for i, item in enumerate(architecture, start=1):
        st.write(f"**{i}.** {item}")

    st.divider()
    st.subheader("Supported Public Inputs")
    input_col1, input_col2, input_col3 = st.columns(3)
    with input_col1:
        st.info("📄 CSV\n\nStructured scientific data")
    with input_col2:
        st.info("🖼️ Image\n\nScientific image data")
    with input_col3:
        st.info("📈 Time-Series\n\nSignal-based data")

    st.divider()
    st.subheader("Responsible Research")
    st.markdown(
        """
        - Raw input preservation
        - Data provenance
        - Technical validation
        - Quality-control checks
        - Human review
        - Research-oriented anomaly prioritization
        """
    )
    st.warning(
        "This platform is not a clinical diagnostic system, "
        "medical decision tool, or flight-certified spacecraft system."
    )

# ============================================================
# DATA UPLOAD
# ============================================================
elif page == "📥 Data Upload":
    st.header("📥 Data Upload")
    st.write(
        "Upload a supported public input file for technical inspection "
        "and exploratory processing."
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=[
            "csv",
            "png",
            "jpg",
            "jpeg",
            "bmp",
            "tif",
            "tiff",
            "webp",
            "txt",
            "dat",
        ],
    )

    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        input_type = detect_input_type(filename)
        raw_hash = calculate_sha256(raw_bytes)

        st.session_state.uploaded_data = raw_bytes
        st.session_state.uploaded_name = filename
        st.session_state.uploaded_type = input_type
        st.session_state.uploaded_hash = raw_hash
        st.session_state.uploaded_size = len(raw_bytes)

        st.success(f"Loaded: {filename}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Input Type", input_type)
        with col2:
            st.metric("File Size", format_bytes(len(raw_bytes)))
        with col3:
            st.metric("Integrity Hash", raw_hash[:12] + "...")

        st.divider()
        st.subheader("Raw Input Information")
        metadata = {
            "filename": filename,
            "input_type": input_type,
            "file_size_bytes": len(raw_bytes),
            "sha256": raw_hash,
            "received_at_utc": utc_timestamp(),
            "raw_data_immutable": True,
        }
        st.json(metadata)

        # ----------------------------------------------------
        # CSV PREVIEW & MODULES 18-22 EXECUTION
        # ----------------------------------------------------
        if input_type == "CSV":
            try:
                import pandas as pd
                dataframe = pd.read_csv(io.BytesIO(raw_bytes))
                st.subheader("CSV Preview")
                st.dataframe(
                    dataframe.head(100),
                    use_container_width=True,
                )
                st.caption(
                    f"Rows: {len(dataframe):,} | "
                    f"Columns: {len(dataframe.columns):,}"
                )

                # Execute Modules 18-22 for numeric signals
                numeric_cols = dataframe.select_dtypes(include=np.number).columns
                if len(numeric_cols) > 0 and ANALYTICS_AVAILABLE:
                    signal_data = dataframe[numeric_cols[0]].dropna().values.astype(np.float64)
                    anomaly_res = calculate_anomaly_score_1d(signal_data)
                    transition_res = analyze_transition_1d(signal_data)
                    uncertainty_res = evaluate_uncertainty_bounds(anomaly_res.get("anomaly_score", 0.0), sample_size=len(signal_data))
                    explain_res = generate_explainability_report(
                        dataset_id=filename,
                        metric_values={"anomaly_score": anomaly_res.get("anomaly_score", 0.0)},
                        confidence=uncertainty_res.get("confidence", 0.85)
                    )
                    st.session_state.analytics_results = {
                        "anomaly": anomaly_res,
                        "transition": transition_res,
                        "uncertainty": uncertainty_res,
                        "explainability": explain_res
                    }
            except Exception as exc:
                st.error(
                    f"CSV preview could not be generated: {exc}"
                )

        # ----------------------------------------------------
        # IMAGE PREVIEW & MODULES 18-22 EXECUTION
        # ----------------------------------------------------
        elif input_type == "IMAGE":
            try:
                from PIL import Image
                image = Image.open(io.BytesIO(raw_bytes))
                st.subheader("Image Preview")
                st.image(
                    image,
                    caption=filename,
                    use_container_width=True,
                )
                st.write(
                    {
                        "format": image.format,
                        "mode": image.mode,
                        "width": image.width,
                        "height": image.height,
                    }
                )

                # Execute Modules 18-22 for 2D image matrix
                if ANALYTICS_AVAILABLE:
                    gray_img = np.array(image.convert("L"), dtype=np.float64)
                    anomaly_res = calculate_anomaly_score_2d(gray_img)
                    transition_res = analyze_transition_2d(gray_img)
                    uncertainty_res = evaluate_uncertainty_bounds(anomaly_res.get("anomaly_score", 0.0), sample_size=gray_img.size)
                    explain_res = generate_explainability_report(
                        dataset_id=filename,
                        metric_values={"anomaly_score": anomaly_res.get("anomaly_score", 0.0)},
                        confidence=uncertainty_res.get("confidence", 0.85)
                    )
                    st.session_state.analytics_results = {
                        "anomaly": anomaly_res,
                        "transition": transition_res,
                        "uncertainty": uncertainty_res,
                        "explainability": explain_res
                    }
            except Exception as exc:
                st.error(
                    f"Image preview could not be generated: {exc}"
                )

        # ----------------------------------------------------
        # TIME-SERIES PREVIEW & MODULES 18-22 EXECUTION
        # ----------------------------------------------------
        elif input_type == "TIME-SERIES":
            st.subheader("Time-Series Input")
            try:
                text_preview = raw_bytes.decode(
                    "utf-8", errors="replace"
                )
                st.code(
                    text_preview[:5000],
                    language="text",
                )

                # Execute Modules 18-22 for Time-Series
                signal_vals = []
                for line in text_preview.splitlines():
                    try:
                        signal_vals.append(float(line.strip()))
                    except ValueError:
                        continue

                if len(signal_vals) > 0 and ANALYTICS_AVAILABLE:
                    signal_arr = np.array(signal_vals, dtype=np.float64)
                    anomaly_res = calculate_anomaly_score_1d(signal_arr)
                    transition_res = analyze_transition_1d(signal_arr)
                    uncertainty_res = evaluate_uncertainty_bounds(anomaly_res.get("anomaly_score", 0.0), sample_size=len(signal_arr))
                    explain_res = generate_explainability_report(
                        dataset_id=filename,
                        metric_values={"anomaly_score": anomaly_res.get("anomaly_score", 0.0)},
                        confidence=uncertainty_res.get("confidence", 0.85)
                    )
                    st.session_state.analytics_results = {
                        "anomaly": anomaly_res,
                        "transition": transition_res,
                        "uncertainty": uncertainty_res,
                        "explainability": explain_res
                    }
            except Exception as exc:
                st.error(
                    f"Time-series preview failed: {exc}"
                )

        # ----------------------------------------------------
        # MODULES 18-22 ANALYTICS DASHBOARD CARD
        # ----------------------------------------------------
        if st.session_state.analytics_results is not None:
            st.divider()
            st.subheader("🔬 Modules 18–22 Connected Analytics Output")
            res = st.session_state.analytics_results
            
            a_score = res["anomaly"].get("anomaly_score", 0.0)
            a_rank = res["anomaly"].get("anomaly_rank", "LOW")
            t_score = res["transition"].get("transition_score", 0.0)
            conf = res["uncertainty"].get("confidence", 0.85)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Anomaly Score (M20)", f"{a_score:.4f}", f"Rank: {a_rank}")
            with c2:
                st.metric("Transition Score (M19)", f"{t_score:.4f}")
            with c3:
                st.metric("Uncertainty Confidence (M21)", f"{conf*100:.1f}%")

            with st.expander("📊 Explainability Report (M22)", expanded=False):
                st.json(res["explainability"])

    else:
        st.info(
            "Upload a CSV, image, or supported time-series file "
            "to begin."
        )

# ============================================================
# DATA QUALITY
# ============================================================
elif page == "🔬 Data Quality":
    st.header("🔬 Data Quality & Integrity")

    if st.session_state.uploaded_data is None:
        st.info(
            "Please upload a dataset from the Data Upload page first."
        )
    else:
        raw_bytes = st.session_state.uploaded_data
        st.success("Raw input received.")

        checks = {
            "File received": True,
            "Raw data preserved": True,
            "SHA-256 generated": True,
            "Input type detected": (
                st.session_state.uploaded_type != "UNKNOWN"
            ),
            "Analytics Core (18-22) Connected": ANALYTICS_AVAILABLE,
            "Human review available": True,
        }

        for check_name, result in checks.items():
            if result:
                st.success(f"✓ {check_name}")
            else:
                st.error(f"✗ {check_name}")

        st.divider()
        st.subheader("Provenance")
        st.json(
            {
                "source_name": st.session_state.uploaded_name,
                "input_type": st.session_state.uploaded_type,
                "size_bytes": st.session_state.uploaded_size,
                "sha256": st.session_state.uploaded_hash,
                "analytics_active": ANALYTICS_AVAILABLE,
                "received_at_utc": utc_timestamp(),
                "raw_data_immutable": True,
            }
        )

        st.divider()
        st.caption(
            "Quality-control results shown here are technical "
            "checks and should not be interpreted as scientific "
            "or medical conclusions."
        )

# ============================================================
# VISUALIZATION
# ============================================================
elif page == "📊 Visualization":
    st.header("📊 Visualization")

    if st.session_state.uploaded_data is None:
        st.info(
            "Upload a dataset first to generate exploratory visualization."
        )
    else:
        input_type = st.session_state.uploaded_type
        raw_bytes = st.session_state.uploaded_data

        if input_type == "CSV":
            try:
                import pandas as pd
                import matplotlib.pyplot as plt

                dataframe = pd.read_csv(io.BytesIO(raw_bytes))
                numeric_columns = dataframe.select_dtypes(
                    include="number"
                ).columns.tolist()

                if numeric_columns:
                    selected_column = st.selectbox(
                        "Select numeric signal",
                        numeric_columns,
                    )
                    fig = plt.figure()
                    plt.plot(dataframe[selected_column].values)
                    plt.title(f"Exploratory Signal: {selected_column}")
                    plt.xlabel("Sample")
                    plt.ylabel(selected_column)
                    st.pyplot(fig)
                    st.caption("Exploratory visualization only.")
                else:
                    st.warning("No numeric columns were detected.")
            except Exception as exc:
                st.error(f"Visualization failed: {exc}")

        elif input_type == "IMAGE":
            try:
                from PIL import Image
                image = Image.open(io.BytesIO(raw_bytes))
                st.image(
                    image,
                    caption="Input Image",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Image visualization failed: {exc}")
        else:
            st.info(
                "Advanced time-series visualization is under development."
            )

        if st.session_state.analytics_results is not None:
            st.divider()
            st.subheader("📊 Analytics Summary Matrix (Modules 18-22)")
            st.json(st.session_state.analytics_results["explainability"])

        st.divider()
        st.warning(
            "Advanced entropy, variance, gradient, CSI and anomaly "
            "visualization modules will be connected as development continues."
        )

# ============================================================
# SPACE MODE
# ============================================================
elif page == "🛰️ Space Mode":
    st.header("🛰️ NASA / Space Mode")
    st.info("Space Mode is an active development area.")

    st.subheader("Planned Public Workflow")
    st.write(
        """
        NASA dataset → Input Adapter → Unified Data Layer → Technical QC → Feature Interface → Analytics → Visualization
        """
    )

    st.divider()
    st.subheader("NASA Data Integration")
    st.warning(
        "NASA dataset loaders and space-specific processing modules "
        "are currently under development."
    )
    st.markdown(
        """
        Planned sources include compatible NASA open datasets and NASA API-accessible data products.
        """
    )

# ============================================================
# BIOMEDICAL MODE
# ============================================================
elif page == "🩻 Biomedical Mode":
    st.header("🩻 Biomedical Research Mode")
    st.info(
        "Biomedical functionality is intended for research validation "
        "and technical data exploration."
    )

    st.subheader("Current Scope")
    st.markdown(
        """
        - Image and structured-data exploration
        - Technical quality assessment
        - Research visualization
        - Human review
        """
    )

    st.warning(
        "This platform does not provide clinical diagnosis, "
        "medical advice, or automated disease detection."
    )
    st.caption(
        "DICOM adapter and biomedical validation modules are under development."
    )

# ============================================================
# LIVE MODE
# ============================================================
elif page == "🎥 Live Mode":
    st.header("🎥 Live / Demonstration Mode")
    st.info("Live imaging is planned as an optional demonstration mode.")

    st.subheader("Development Status")
    st.warning(
        "Video adapter, stream controller, frame processor, "
        "live metrics, and live heatmap modules are under development."
    )
    st.caption(
        "Live mode is a research demonstration and is not a clinical "
        "or operational diagnostic system."
    )

# ============================================================
# ABOUT
# ============================================================
elif page == "ℹ️ About":
    st.header("ℹ️ About D³ VITAL-X")
    st.markdown(
        """
        ### D³ VITAL-X Space Intelligence Platform
        **D³ VITAL-X BANGLADESH**

        An independent research-oriented prototype designed to support scientific data exploration through a unified, lightweight framework.

        ### Current Focus
        - Scientific data ingestion
        - Unified data representation
        - Technical validation
        - Quality control
        - Exploratory visualization
        - Human-centered anomaly prioritization

        ### Development Status
        **ACTIVE DEVELOPMENT**

        The public repository contains framework components and interfaces. Proprietary intelligence-core implementation is not publicly exposed.
        """
    )

    st.divider()
    st.subheader("Responsible Use")
    st.warning(
        "Research prototype only. Not a clinical diagnostic system, "
        "medical decision tool, or flight-certified spacecraft system."
    )

    st.divider()
    st.caption("D³ VITAL-X BANGLADESH • NASA Space Apps Challenge 2026")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "D³ VITAL-X Space Intelligence Platform | "
    "Independent Research Prototype | "
    f"{PROJECT_STATUS}"
)
