from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="lesion-segmentor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "nibabel>=4.0.0",
        "appdirs>=1.4.4",
    ],
    entry_points={
        "console_scripts": [
            "lesion-segmentor=lesion_segmentor.cli:main",
        ],
    },
    python_requires=">=3.8",
    include_package_data=True,
    data_files=[
        ('lesion_segmentor/docker', [
            'lesion_segmentor/docker/Dockerfile',
            'lesion_segmentor/docker/docker-compose.yml',
            'lesion_segmentor/docker/.dockerignore',
            'lesion_segmentor/docker/.env'
        ]),
        ('lesion_segmentor/scripts', [
            'lesion_segmentor/scripts/docker_segment.sh'
        ]),
        ('lesion_segmentor', [
            'lesion_segmentor/inference.py',
            'lesion_segmentor/model.py',
            'lesion_segmentor/utils.py',
            'lesion_segmentor/download.py'
        ])
    ],
    description="A tool for automated lesion segmentation in FLAIR MRI scans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Soumen Ghosh",
    author_email="soumen02@gmail.com",
    url="https://github.com/soumen02/lesion-segmentator",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
) 