from typing import List


def get_device(prefer_gpu: bool = True) -> str:
    """
    Returns 'cuda' if prefer_gpu is True and a CUDA-capable GPU is available via PyTorch,
    otherwise returns 'cpu'.
    """
    if not prefer_gpu:
        return "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def get_onnx_providers(prefer_gpu: bool = True) -> List[str]:
    """
    Returns ordered ONNX Runtime execution providers based on hardware availability.
    """
    if not prefer_gpu:
        return ["CPUExecutionProvider"]
    try:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "CUDAExecutionProvider" in available:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    except ImportError:
        pass
    return ["CPUExecutionProvider"]
