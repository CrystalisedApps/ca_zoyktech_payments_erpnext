from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __init__.py
from zoyktech_zambia_payments import __version__ as version

setup(
    name="zoyktech_zambia_payments",
    version=version,
    description="Payment Gateway Integration for Zambia",
    author="Marty Muhanga",
    author_email="marty@crystalisedapps.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)