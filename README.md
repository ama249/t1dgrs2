# t1dgrs2

---

Generate a Type 1 Diabetes Genetic Risk Score that accounts for interactions between HLA-DQ variants.

---

## Requirements

- Linux environment (Debian-based or RHEL-based)
- The Linux x86_64 installations of any one of the following:
  - [Miniforge](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh)
  - [Mambaforge](https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh)
  - An existing Anaconda installation (compatibility-based issues may occur if the `conda` package is very old, latest version would be preferable)
- PLINK v1.90 (minor version changes acceptable) command-line tool (bundled into the main package, no manual installation required for this)

> Note: Please consult your local server admin to resolve conflicting installations of PLINK.

After setting up Anaconda, creating and activating a separate environment is highly recommended to avoid dependency conflicts with other packages already installed on the system, Python or otherwise.

```{bash}
conda env create -n <new_env_name> python
conda activate <new_env_name>
```
or the following, if Mambaforge was installed:
```{bash}
mamba env create -n <new_env_name> python
mamba activate <new_env_name>
```

---

## Usage

After activating the environment created in the previous step, please install the `t1dgrs2` package from the [Bioconda repository](https://anaconda.org/bioconda/repo/) using the following command:

```{bash}
conda install -n <new_env_name> -c bioconda t1dgrs2
```
or
```{bash}
mamba install -n <new_env_name> -c bioconda t1dgrs2
```

Once the package is installed, please use the `-h` flag to output the help text for more information:

```{bash}
python -m t1dgrs2 -h
```

The package has an built-in executable script, so simply run the module directly to generate the scores:

```{bash}
python -m t1dgrs2 -b /path/to/plink/bfiles/prefix -c /path/to/t1dgrs2_settings.yml -o /path/to/output/prefix
```

## Execution

To highlight the flow of the program:

- A log file `t1dgrs2.log` will be created at your current working directory, to track execution progress in real-time.
- According to the value for argument `-b` / `--bfile`:
  - The input PLINK format files must be within the directory tree `/path/to/plink/bfiles/`.
  - The file names themselves must be of the form `prefix.bed`, `prefix.bim` and `prefix.fam`.
    - All three files must exist for successful execution.
- According to the value for argument `-o` / `--output`:
  - The final output files will be created within the directory tree `/path/to/output/`.
  - The file names themselves will be of the form `prefix_FILE1`, `prefix_FILE2`, etc.

If the `-o` argument is not set on execution, output files will be created as `output_FILE1`, `output_FILE2`, etc. at your current working directory.

---

## Maintained by

Complex Traits Genomics of Diabetes group<br>
Department of Clinical and Biomedical Sciences<br>
University of Exeter Medical School<br>
St Luke's Campus<br>
Heavitree Road<br>
Exeter<br>
EX1 2LU.
