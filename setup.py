from setuptools import setup

from setuptools import find_packages


setup(
    name="prd-data",
    package_dir={"": "src"},
    version="0.1.0",
    packages=find_packages(where="src", exclude=("test*", "testing*")),
    include_package_data=True,
    package_data={
        "prd-data": [
            "*.zip",
        ]
    },
)
