from setuptools import find_packages, setup

setup(
    name="braillevision",
    version="0.1.0",
    description="Computer vision pipeline for reading physical Braille images.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.11",
)
