from os import linesep
from os.path import dirname
from yaml import safe_load
from re import compile, search
from setuptools import setup
from versioneer import get_cmdclass
from tempfile import NamedTemporaryFile


def get_conda_metadata(conda_meta_file: str) -> dict:
    with open(conda_meta_file, mode="r") as actual, NamedTemporaryFile(
        mode="r+", dir=dirname(conda_meta_file), encoding="UTF-8", newline=linesep
    ) as temp:
        metadata_vars = {}
        metadata_rgx = compile(r"""^{%\s+set\s+(\S+)\s+=\s+(\S+)\s+%}""")
        for i, line in enumerate(actual):
            m = search(pattern=metadata_rgx, string=line)
            if m:
                metadata_vars[i] = (m.groups()[0], m.groups()[1].strip('"'))
            else:
                temp.write(line)
        temp.seek(0)
        conda_metadata = safe_load(temp)
    for _, (metavar_key, metavar_value) in metadata_vars.items():
        if metavar_key == "org":
            for k1, k2 in [("source", "url"), ("about", "home")]:
                conda_metadata[k1][k2] = conda_metadata[k1][k2].replace(
                    f"{{{{ {metavar_key} }}}}", metavar_value
                )
        elif metavar_key == "pkg_name":
            for k1, k2 in [("package", "name"), ("source", "url"), ("about", "home")]:
                conda_metadata[k1][k2] = conda_metadata[k1][k2].replace(
                    f"{{{{ {metavar_key} }}}}", metavar_value
                )
        elif metavar_key == "version":
            for k1, k2 in [("package", "version"), ("source", "url")]:
                conda_metadata[k1][k2] = conda_metadata[k1][k2].replace(
                    f"{{{{ {metavar_key} }}}}", metavar_value
                )
        elif metavar_key == "build_num":
            for k1, k2 in [("build", "number")]:
                conda_metadata[k1][k2] = conda_metadata[k1][k2].replace(
                    f"{{{{ {metavar_key} }}}}", metavar_value
                )
    return conda_metadata


conda_metadata = get_conda_metadata("conda.recipe/meta.yaml")
requirements = conda_metadata["requirements"]["run"]

# Read in the requirements.txt file
# with open("requirements.txt") as f:
#     requirements = []
#     for library in f.read().splitlines():
#         requirements.append(library)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="t1dgrs2",
    version=0,
    cmdclass=get_cmdclass(),
    description="Generate a Type 1 Diabetes Genetic Risk Score that accounts for interactions between HLA-DQ variants.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNUv3",
    author="Ankit Arni",
    author_email="A.M.Arni@exeter.ac.uk",
    url="https://github.com/ama249/t1dgrs2",
    packages=["t1dgrs2"],
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
