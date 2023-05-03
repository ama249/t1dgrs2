# t1dgrs2

## **CAUTION: FOR INTERNAL USE ONLY!**

---

Generate a Type 1 Diabetes Genetic Risk Score that accounts for interactions between HLA-DQ variants.

---

## Requirements

- Linux environment (Debian-based or RHEL-based)
- The Linux x86_64 installations of either one of the following Anaconda flavours:
  - [Miniforge](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh)
  - [Mambaforge](https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh)
  - An existing Anaconda installation (compatibility-based issues may occur if the `conda` package is very old, latest version would be preferable)
- PLINK v1.90 (minor version changes acceptable) command-line tool (added to environment file, no separate installation required)

After setting up Anaconda, creating and activating a separate environment is highly recommended. Please use the following command after downloading the file `config/conda_env.yml` to the local machine:

```{bash}
conda env create -f conda_env.yml
conda activate t1dgrs2
```
or the following, if Mambaforge was installed:
```{bash}
mamba env create -f conda_env.yml
mamba activate t1dgrs2
```

---

## Usage

After activating the environment created in the previous step, please install the package from the GitHub repository using the following command:

```{bash}
pip install git+https://github.com/ama249/t1dgrs2.git
```

A main script `generate_t1dgrs2.py` has been provided, please download this to actually generate the final scores.

```{bash}
python generate_t1dgrs2.py -b /path/to/plink/bfiles -c t1dgrs2_settings.yml -o /path/to/output/prefix
```

A log file `t1dgrs2.log` will be created at the current working directory, the following command can be used to track the progress of the script execution in real-time:

```{bash}
tail -f t1dgrs2.log
```

---

## Maintained by

Complex Traits Genomics of Diabetes group<br>
Department of Clinical and Biomedical Sciences<br>
University of Exeter Medical School<br>
St Luke's Campus<br>
Heavitree Road<br>
Exeter<br>
EX1 2LU.
