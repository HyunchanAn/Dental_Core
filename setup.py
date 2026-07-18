from setuptools import setup, find_packages

setup(
    name="dental_core",
    version="0.1.0",
    description="Core utilities and common modules for the Dental project.",
    author="Hyunchan An",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "opencv-python",
        "matplotlib",
        # Note: onnxruntime and torch are intentionally left out here to keep
        # this core library perfectly lightweight and universally injectable.
    ],
    python_requires=">=3.9",
)
