from setuptools import setup, find_packages

setup(
    name="ufaflow",
    version="0.1.0",
    description="UfaFlow — lightweight L4/L7 load balancer (MVP)",
    packages=find_packages(),
    install_requires=[
        "PyYAML",
        # optional: uvloop improves async performance if installed
    ],
    entry_points={
        "console_scripts": [
            "ufaflow=ufaflow.cli:main"
        ]
    },
    author="halif",
    license="MIT",
)