from setuptools import setup

from setuptools import find_packages
from setuptools.command.build_py import build_py

import os 
import zipfile 

from enum import Enum

PACKAGE_NAME = "prd-data" 

class my_build_py(build_py):
    """Custom build step to unzip packaged parquets."""
    def run(self) -> None: 

        src_dir = os.path.abspath(os.path.join('src', PACKAGE_NAME))
        zip_path = os.path.join(src_dir, 'data.parquet.zip') 

        if not os.path.exists(zip_path):
            error_msg = f"Missing '{zip_path}. Ensure package was built correctly."
            raise FileNotFoundError(error_msg)

        extract_to = src_dir
        # os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref: 
            zip_ref.extractall(extract_to)
        
        super().run()

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=("test*", "testing*", "tests*")),
    cmdclass={'build_py':my_build_py}, 
    include_package_data=True,
    package_data={
        "prd-data": [
            "*.zip",
        ]
    },
)
