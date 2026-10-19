import os
from typing import Optional, Union, List
import numpy as np
import cv2


PHI_ATTRIBUTES: List[str] = [
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientBirthTime",
    "PatientSex",
    "PatientAge",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "OtherPatientIDs",
    "OtherPatientNames",
    "InstitutionName",
    "InstitutionAddress",
    "ReferringPhysicianName",
    "PerformingPhysicianName",
    "OperatorsName",
    "AccessionNumber",
    "StudyID",
]


def apply_windowing(
    image: np.ndarray,
    window_center: float,
    window_width: float,
) -> np.ndarray:
    """
    Applies radiological windowing (level/width) to convert a 16-bit/float medical image
    into an 8-bit unsigned integer grayscale array [0, 255].
    """
    if window_width <= 0:
        raise ValueError("window_width must be strictly positive.")

    img_float = image.astype(np.float32)
    lower = window_center - (window_width / 2.0)
    upper = window_center + (window_width / 2.0)

    windowed = np.clip(img_float, lower, upper)
    normalized = ((windowed - lower) / window_width) * 255.0
    return np.round(normalized).astype(np.uint8)


def strip_phi_tags(dicom_dataset):
    """
    Anonymizes Protected Health Information (PHI) fields on a pydicom Dataset
    or dictionary-like metadata object in place and returns it.
    """
    if dicom_dataset is None:
        return None

    if isinstance(dicom_dataset, dict):
        for attr in PHI_ATTRIBUTES:
            if attr in dicom_dataset:
                dicom_dataset[attr] = "ANONYMIZED"
        return dicom_dataset

    for attr in PHI_ATTRIBUTES:
        if hasattr(dicom_dataset, attr):
            try:
                setattr(dicom_dataset, attr, "ANONYMIZED")
            except Exception:
                pass

    if hasattr(dicom_dataset, "remove_private_tags"):
        try:
            dicom_dataset.remove_private_tags()
        except Exception:
            pass

    return dicom_dataset


def load_medical_image(
    path: Union[str, os.PathLike],
    window_center: Optional[float] = None,
    window_width: Optional[float] = None,
    anonymize: bool = True,
) -> np.ndarray:
    """
    Loads a medical radiograph from a DICOM (.dcm/.dicom) or standard image file (.png/.jpg/.tif).
    Applies optional 16-bit windowing if window_center and window_width are provided,
    or normalizes high-bit-depth arrays to 8-bit uint8.
    """
    path_str = str(path)
    if not os.path.exists(path_str):
        raise FileNotFoundError(f"Medical image file not found: {path_str}")

    ext = os.path.splitext(path_str)[1].lower()
    if ext in (".dcm", ".dicom"):
        try:
            import pydicom
        except ImportError as exc:
            raise ImportError(
                "pydicom is required to load DICOM files. Install with `pip install pydicom`."
            ) from exc

        ds = pydicom.dcmread(path_str)
        if anonymize:
            strip_phi_tags(ds)

        pixel_array = ds.pixel_array.astype(np.float32)

        slope = float(getattr(ds, "RescaleSlope", 1.0))
        intercept = float(getattr(ds, "RescaleIntercept", 0.0))
        pixel_array = pixel_array * slope + intercept

        wc = window_center
        ww = window_width
        if wc is None and hasattr(ds, "WindowCenter"):
            raw_wc = ds.WindowCenter
            wc = float(raw_wc[0]) if isinstance(raw_wc, (list, tuple)) or hasattr(raw_wc, "__iter__") else float(raw_wc)
        if ww is None and hasattr(ds, "WindowWidth"):
            raw_ww = ds.WindowWidth
            ww = float(raw_ww[0]) if isinstance(raw_ww, (list, tuple)) or hasattr(raw_ww, "__iter__") else float(raw_ww)

        if wc is not None and ww is not None and ww > 0:
            img_8bit = apply_windowing(pixel_array, wc, ww)
        else:
            p_min = float(np.min(pixel_array))
            p_max = float(np.max(pixel_array))
            if p_max > p_min:
                img_8bit = np.round(((pixel_array - p_min) / (p_max - p_min)) * 255.0).astype(np.uint8)
            else:
                img_8bit = np.zeros_like(pixel_array, dtype=np.uint8)

        if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
            img_8bit = 255 - img_8bit

        return img_8bit

    raw = cv2.imread(path_str, cv2.IMREAD_UNCHANGED)
    if raw is None:
        raise ValueError(f"Failed to decode image file: {path_str}")

    if raw.dtype == np.uint16 or raw.dtype == np.int16 or raw.dtype == np.float32:
        if window_center is not None and window_width is not None:
            return apply_windowing(raw, window_center, window_width)
        r_min = float(np.min(raw))
        r_max = float(np.max(raw))
        if r_max > r_min:
            return np.round(((raw.astype(np.float32) - r_min) / (r_max - r_min)) * 255.0).astype(np.uint8)
        return np.zeros_like(raw, dtype=np.uint8)

    if window_center is not None and window_width is not None:
        return apply_windowing(raw, window_center, window_width)

    return raw
