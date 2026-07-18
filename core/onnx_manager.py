import os
import gc

class ONNXManager:
    """
    단일 런타임 추론 엔진 (ONNX 기반)
    16GB RAM 환경에서도 여러 모델을 스와핑하며 추론할 수 있도록 최적화됨.
    """
    
    def __init__(self):
        self.models = {}
        try:
            import onnxruntime as ort
            self.ort = ort
            # GPU 사용 가능 여부 확인
            providers = ort.get_available_providers()
            if 'CUDAExecutionProvider' in providers:
                self.providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            else:
                self.providers = ['CPUExecutionProvider']
            print(f"ONNX Runtime initialized with providers: {self.providers}")
        except ImportError:
            print("Warning: onnxruntime is not installed. Inference will fail.")
            self.ort = None
            self.providers = []

    def register_model(self, name: str, onnx_path: str):
        """
        모델의 경로만 등록합니다. 메모리(RAM)에 미리 올리지 않습니다.
        """
        if not os.path.exists(onnx_path):
            print(f"Warning: ONNX file not found: {onnx_path}")
            return False
            
        self.models[name] = {
            'path': onnx_path,
            'session': None
        }
        return True

    def load_to_gpu(self, name: str):
        """
        필요한 시점에만 해당 모델의 세션을 생성(GPU/CPU 로드)하여 반환합니다.
        다른 모델 세션이 열려있다면 닫아서 VRAM/RAM을 확보합니다.
        """
        if name not in self.models:
            raise ValueError(f"Model {name} is not registered.")
            
        if self.ort is None:
            raise RuntimeError("onnxruntime is not available.")
            
        # 기존에 열려있는 세션이 자신이 아니라면 모두 해제 (VRAM 최적화)
        self.clear_cache(exclude=name)
        
        # 이미 로드되어 있다면 재사용
        if self.models[name]['session'] is not None:
            return self.models[name]['session']
            
        # 새로 세션 생성 (로드)
        print(f"Loading {name} ONNX session into memory/VRAM...")
        sess = self.ort.InferenceSession(self.models[name]['path'], providers=self.providers)
        self.models[name]['session'] = sess
        return sess
        
    def clear_cache(self, exclude=None):
        """
        현재 메모리에 올라와 있는 세션을 해제하고 가비지 컬렉션을 수행합니다.
        """
        cleared = False
        for k, v in self.models.items():
            if k != exclude and v['session'] is not None:
                # onnxruntime InferenceSession은 명시적 close()가 없으나, 참조를 끊으면 해제됨
                v['session'] = None
                cleared = True
                
        if cleared:
            gc.collect()
