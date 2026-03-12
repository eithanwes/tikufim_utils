from setuptools import find_packages, setup

setup(
    name="tikufim_utils",
    version="0.1.0",
    description="Utility functions for tikufim passenger counts",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # keep minimal; see requirements.txt for pinned versions
    ],
    zip_safe=False,
)
