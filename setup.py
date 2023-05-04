from setuptools import setup
import versioneer

# Read in the requirements.txt file
with open("requirements.txt") as f:
    requirements = []
    for library in f.read().splitlines():
        requirements.append(library)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="t1dgrs2",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Generate a Type 1 Diabetes Genetic Risk Score that accounts for interactions between HLA-DQ variants.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNUv3",
    author="Ankit Arni",
    author_email="A.M.Arni@exeter.ac.uk",
    url="https://github.com/ama249/t1dgrs2",
    packages=["t1dgrs2"],
    # entry_points={
    #     "console_scripts": [
    #         "t1dgrs2=t1dgrs2.cli:cli"
    #     ]
    # },
    python_requires=">=3.11.0",
    install_requires=requirements,
    include_package_data=True,
    keywords="t1dgrs2",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
)
