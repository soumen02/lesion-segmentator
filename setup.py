from setuptools import setup, find_packages

setup(
    name="lesion_segmentor",
    version="0.1.0",
    packages=find_packages(include=['lesion_segmentor', 'lesion_segmentor.*', 'scripts']),
    install_requires=[
        "monai>=1.2.0",
        "torch>=1.13.0",
        "nibabel>=4.0.0",
        "numpy>=1.21.0",
        "gdown>=4.7.1",  # For Google Drive downloads
        "monailabel>=0.7.0",
    ],
    entry_points={
        'console_scripts': [
            'segment_lesions=scripts.segment_lesions:main',
        ],
    },
    python_requires=">=3.8",
) 