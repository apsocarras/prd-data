from setuptools import setup

from setuptools import find_packages
from setup.tools.command.build_by import build_py

import os 
import zipfile 

# class my_build_py(build_py):
#     """Custom build step to unzip packaged parquets."""
#     def run(self) -> None: 
#         zip_path = os.path.join('src','prd-data', 'data.parquet.zip') 
#         with ZipFile(zip_path) as myzip: 
                
        

    
setup(
    name="prd-data",
    package_dir={"": "src"},
    version="0.1.0",
    packages=find_packages(where="src", exclude=("test*", "testing*")),
    cmd_class={'build_py':my_build_py}
    include_package_data=True,
    package_data={
        "prd-data": [
            "*.zip",
        ]
    },
)
