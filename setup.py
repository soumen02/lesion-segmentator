from setuptools import setup, find_packages

setup(
    name="lesion-segmentor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "nibabel>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lesion-segmentor=lesion_segmentor.cli:main",
        ],
    },
    python_requires=">=3.8",
    include_package_data=True,
    # Include the docker and script files in the package
    package_data={
        "lesion_segmentor": [
            "scripts/*",
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
        ],
    },
    description="A tool for automated lesion segmentation in FLAIR MRI scans",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/lesion_segmentor",
) 