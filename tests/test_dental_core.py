import logging
import os
import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dental_core import (
    apply_windowing,
    strip_phi_tags,
    load_medical_image,
    apply_clahe,
    calculate_iou,
    map_lesions_to_fdi,
    get_logger,
    get_device,
    get_onnx_providers,
    ONNXManager,
)


def test_apply_windowing_16bit_to_8bit():
    img_16 = np.array([[0, 1000, 2000], [3000, 4000, 5000]], dtype=np.uint16)
    out = apply_windowing(img_16, window_center=2000.0, window_width=2000.0)
    assert out.dtype == np.uint8
    assert out.shape == img_16.shape
    assert out[0, 0] == 0
    assert out[0, 1] == 0
    assert out[0, 2] == 128
    assert out[1, 0] == 255
    assert out[1, 2] == 255


def test_apply_windowing_invalid_width():
    img = np.zeros((4, 4), dtype=np.uint16)
    with pytest.raises(ValueError):
        apply_windowing(img, window_center=100.0, window_width=0.0)


def test_strip_phi_tags_dict_and_object():
    meta_dict = {
        "PatientName": "John Doe",
        "PatientID": "12345",
        "Modality": "PX",
    }
    cleaned = strip_phi_tags(meta_dict)
    assert cleaned["PatientName"] == "ANONYMIZED"
    assert cleaned["PatientID"] == "ANONYMIZED"
    assert cleaned["Modality"] == "PX"

    class DummyDataset:
        def __init__(self):
            self.PatientName = "Jane Doe"
            self.InstitutionName = "Test Clinic"
            self.Rows = 512
            self.private_removed = False

        def remove_private_tags(self):
            self.private_removed = True

    ds = DummyDataset()
    strip_phi_tags(ds)
    assert ds.PatientName == "ANONYMIZED"
    assert ds.InstitutionName == "ANONYMIZED"
    assert ds.Rows == 512
    assert ds.private_removed is True


def test_load_medical_image_png_8bit_and_16bit(tmp_path):
    img_8 = np.random.randint(0, 256, size=(32, 32), dtype=np.uint8)
    path_8 = tmp_path / "sample_8bit.png"
    cv2.imwrite(str(path_8), img_8)

    loaded_8 = load_medical_image(path_8)
    assert loaded_8.dtype == np.uint8
    assert loaded_8.shape == (32, 32)

    img_16 = np.linspace(0, 4095, num=32 * 32, dtype=np.uint16).reshape((32, 32))
    path_16 = tmp_path / "sample_16bit.png"
    cv2.imwrite(str(path_16), img_16)

    loaded_16 = load_medical_image(path_16, window_center=2048.0, window_width=1024.0)
    assert loaded_16.dtype == np.uint8
    assert loaded_16.shape == (32, 32)
    assert loaded_16[0, 0] == 0
    assert loaded_16[-1, -1] == 255


def test_load_medical_image_missing_file():
    with pytest.raises(FileNotFoundError):
        load_medical_image("non_existent_medical_file.png")


def test_get_logger():
    logger = get_logger("test_dental_logger", level=logging.DEBUG)
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) >= 1


def test_get_device_and_providers():
    assert get_device(prefer_gpu=False) == "cpu"
    dev = get_device(prefer_gpu=True)
    assert dev in ("cuda", "cpu")

    providers_cpu = get_onnx_providers(prefer_gpu=False)
    assert providers_cpu == ["CPUExecutionProvider"]

    providers_auto = get_onnx_providers(prefer_gpu=True)
    assert "CPUExecutionProvider" in providers_auto


def test_apply_clahe_gray_and_color():
    gray = np.random.randint(50, 150, size=(64, 64), dtype=np.uint8)
    enhanced_gray = apply_clahe(gray)
    assert enhanced_gray.shape == gray.shape
    assert enhanced_gray.dtype == np.uint8

    bgr = np.random.randint(50, 150, size=(64, 64, 3), dtype=np.uint8)
    enhanced_bgr = apply_clahe(bgr)
    assert enhanced_bgr.shape == bgr.shape
    assert enhanced_bgr.dtype == np.uint8


def test_calculate_iou_and_map_lesions_to_fdi():
    lesion_box = [10, 10, 20, 20]
    tooth_box = [5, 5, 25, 25]
    iou = calculate_iou(lesion_box, tooth_box)
    assert iou == pytest.approx(1.0)

    caries_data = {
        "boxes": [[10, 10, 20, 20], [100, 100, 110, 110]],
        "labels": ["Caries", "Periapical"],
    }
    tooth_roi_data = {
        "boxes": [[5, 5, 25, 25], [50, 50, 70, 70]],
        "fdi_labels": ["14", "24"],
    }
    mapped = map_lesions_to_fdi(caries_data, tooth_roi_data)
    assert len(mapped) == 2
    assert mapped[0]["fdi"] == "14"
    assert mapped[0]["lesion_type"] == "Caries"
    assert mapped[1]["fdi"] == "Unknown"


def test_onnx_manager_lifecycle(tmp_path):
    mgr = ONNXManager()
    assert mgr.register_model("missing_model", local_path=str(tmp_path / "nope.onnx")) is False

    dummy_onnx = tmp_path / "dummy.onnx"
    dummy_onnx.write_bytes(b"dummy")
    assert mgr.register_model("dummy_model", local_path=str(dummy_onnx)) is True
    assert "dummy_model" in mgr.models

    mgr.models["dummy_model"]["session"] = object()
    mgr.clear_cache()
    assert mgr.models["dummy_model"]["session"] is None
