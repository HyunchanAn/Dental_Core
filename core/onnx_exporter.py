import os
import torch

def export_yolov8_to_onnx(model_path, output_dir=None, dynamic=True):
    """
    Exports a YOLOv8 PyTorch model (.pt) to ONNX format.
    Requires ultralytics package.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics package is required for YOLOv8 export.")
        return None
        
    if not os.path.exists(model_path):
        print(f"Error: Checkpoint not found at {model_path}")
        return None
        
    print(f"Loading YOLOv8 model from {model_path}...")
    model = YOLO(model_path)
    
    # By default, ultralytics saves the exported model in the same directory as the .pt file
    # or the current working directory.
    print(f"Exporting to ONNX (dynamic={dynamic})...")
    exported_path = model.export(format="onnx", dynamic=dynamic, simplify=True)
    print(f"Export completed successfully. Model saved at: {exported_path}")
    
    return exported_path

def export_classifier_to_onnx(model, dummy_input, output_path, dynamic_batch=True):
    """
    Generic function to export standard PyTorch CNNs (EfficientNet, ResNet) to ONNX.
    """
    import torch
    
    model.eval()
    
    dynamic_axes = None
    if dynamic_batch:
        dynamic_axes = {
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
        
    print(f"Exporting standard PyTorch model to {output_path}...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes=dynamic_axes
    )
    
    print("Export completed successfully.")
    return output_path
