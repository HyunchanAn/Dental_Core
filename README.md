![Status](https://img.shields.io/badge/Status-v0.1.0%20Release-brightgreen "Status") ![Python](https://img.shields.io/badge/Python-3.9%2B-blue "Python") ![Backend](https://img.shields.io/badge/Backend-DICOM%20%2F%20ONNX%20Runtime-blue "Backend") ![License](https://img.shields.io/badge/License-MIT-green "License") ![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD%20Pipeline-passing-brightgreen?logo=github "CI/CD Pipeline")

# Dental_Core: Shared Medical Imaging, Geometry & ONNX Runtime Library (치과 AI 공통 코어 유틸리티)

## 개요

`Dental_Core`는 치과 방사선 AI 파이프라인(`Dental_001` ~ `Dental_015`, `Dental_Panoramic_Reader`) 전반에서 공통으로 사용하는 핵심 유틸리티 및 런타임 관리 라이브러리입니다. DICOM 및 의료 영상 로드(16-bit 윈도잉, PHI 익명화), 전처리(CLAHE), 기하학적 FDI 치아 매핑, 시각화, 디바이스 감지, 표준 로거, ONNX 모델 익스포트 및 VRAM 최적화 세션 스와핑(`ONNXManager`) 기능을 제공합니다.

---

## 주요 기능 및 아키텍처

- `dental_core.io.dicom`
  - `apply_windowing(image, window_center, window_width)`: 16-bit 또는 실수형 의료 영상을 지정된 Window Center / Width 기준으로 8-bit(`uint8`) 배열로 변환합니다.
  - `strip_phi_tags(dicom_dataset)`: DICOM 데이터셋 또는 메타데이터 사전에서 환자 식별 정보(PHI) 태그를 익명화(`ANONYMIZED`)하고 사설 태그를 제거합니다.
  - `load_medical_image(path, window_center=None, window_width=None, anonymize=True)`: `.dcm`/`.dicom`(`pydicom` 연동) 및 일반 8/16-bit 방사선 이미지를 로드하여 정규화된 8-bit 배열을 반환합니다.
- `dental_core.utils.image`
  - `apply_clahe(image, clip_limit=2.0, tile_grid_size=(8, 8))`: 그레이스케일 및 컬러(LAB L-채널) 방사선 영상에 CLAHE 대비 향상 필터를 적용합니다.
- `dental_core.utils.geometry`
  - `calculate_iou(boxA, boxB)`: 병소 박스와 치아 ROI 박스 간 교차 면적 비율(IoA/IoU)을 계산합니다.
  - `map_lesions_to_fdi(caries_data, tooth_roi_data)`: 검출된 병소 바운딩 박스를 FDI 치아 번호 박스에 기하학적으로 매핑합니다.
- `dental_core.utils.viz`
  - `draw_yolo_labels(image_path, label_path, output_path, class_names)`: YOLO 정규화 라벨을 이미지 위에 시각화하여 저장합니다.
  - `bulk_visualize(image_dir, label_dir, output_dir, class_names, limit=20)`: 디렉토리 내 다수의 이미지-라벨 쌍을 일괄 시각화합니다.
- `dental_core.utils.logging`
  - `get_logger(name="dental_core", level=logging.INFO)`: 타임스탬프와 모듈명이 통일된 표준 스트림 로거를 반환합니다.
- `dental_core.utils.device`
  - `get_device(prefer_gpu=True)`: PyTorch CUDA 가용 여부에 따라 `'cuda'` 또는 `'cpu'`를 반환합니다.
  - `get_onnx_providers(prefer_gpu=True)`: ONNX Runtime 가용 프로바이더(`CUDAExecutionProvider`, `CPUExecutionProvider`) 목록을 반환합니다.
- `dental_core.core.onnx_exporter`
  - `export_yolov8_to_onnx(model_path, output_dir=None, dynamic=True)`: Ultralytics YOLO `.pt` 가중치를 ONNX 포맷으로 변환합니다.
  - `export_classifier_to_onnx(model, dummy_input, output_path, dynamic_batch=True)`: PyTorch 분류 모델을 ONNX opset 17로 변환합니다.
- `dental_core.core.onnx_manager`
  - `ONNXManager`: 제한된 VRAM/RAM 환경에서 다중 ONNX 모델을 지연 로드하고 세션을 자동 스와핑하는 추론 매니저입니다.

---

## 벤치마크 및 검증 성능

- `tests/test_dental_core.py`: 16-bit DICOM 윈도잉, PHI 태그 익명화, CLAHE 전처리, IoU 및 FDI 병소 매핑, 표준 로거, 디바이스/ONNX 프로바이더 감지, `ONNXManager` LRU 세션 스와핑 단위 테스트 10건 전원 통과(`10 passed`) 및 GitHub Actions CI 자동 검증 연동 완료.

---

## 데이터셋 출처 및 라이선스

- 본 라이브러리는 순수 소프트웨어 유틸리티 패키지로 별도의 환자 데이터셋이나 딥러닝 가중치를 포함하지 않습니다.
- [소스 코드 라이선스]: 본 프로젝트는 `MIT License` ([LICENSE](LICENSE), `Copyright (c) 2026 Hyunchan An`) 하에 배포됩니다.

---

## 설치 및 실행 방법

### 1. 패키지 설치
```bash
# 로컬 개발자 모드 설치
pip install -e .

# 또는 소비 레포지토리에서 릴리스 태그 고정 설치
pip install git+https://github.com/HyunchanAn/Dental_Core.git@v0.1.0
```

### 2. 단위 테스트 실행
```bash
pytest tests/ -v
```

---

## 참고 문헌 및 연구용 실행 주의사항

- NEMA PS3 / ISO 12052 Digital Imaging and Communications in Medicine (DICOM) Standard (Confidentiality Profile Tags).
- [연구용 실행 주의사항]:
  - 오픈 데이터셋 외 민감 의료데이터 로드 시 반드시 `anonymize=True` (기본값)로 PHI 태그 익명화를 유지하십시오.
