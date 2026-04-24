from setuptools import setup, find_packages

setup(
    name="cortexchain",
    version="0.1.0",
    description="LangChain-style framework for the Lilly Cortex AI API",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "light_client @ git+https://github.com/EliLillyCo/LRL_light_k8s_infra_app_client_python.git@bdf0e2cf27260862b1e5615929e176f62e83a4a4",
    ],
    extras_require={
        "dev": ["pytest", "pytest-mock"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
