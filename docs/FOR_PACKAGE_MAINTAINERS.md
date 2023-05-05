# t1dgrs2

## Important information for maintainers: 

---

### 1. Please create a separate `git` branch before make any changes

Use the following commands to create a new branch before starting to work on a new change:

```{bash}
cd /path/to/local/clone/t1dgrs/
git checkout main
git pull
git checkout -b NEW_BRANCH
```

---

### 2. Please control all versioning of the package using GitHub repository tags

Use the following commands to create a new tag on the ___main___ branch after a new change in ___NEW_BRANCH___ has been merged:

```{bash}
cd /path/to/local/clone/t1dgrs/
git checkout main
git tag VERSION -a -m "Short message about the changes in the new version"
git push origin --tags
```
where ___VERSION___ follows the [PEP-440 convention for final releases](https://peps.python.org/pep-0440/#final-releases).

> This same ___VERSION___ must also be put into the `set version = ""` command at the top of the `bioconda-recipes/recipes/t1dgrs2/meta.yaml` file before creating a pull request on the Bioconda Azure pipeline.

---

### 3. To generate SHA-256 hash for `bioconda-recipes/recipes/t1dgrs2/meta.yaml`

```{bash}
curl -sL https://github.com/<<ORG>>/t1dgrs2/archive/refs/tags/<<VERSION>>.tar.gz | openssl sha256
```
where ___VERSION___ is the same version as the GitHub repository tag.

The SHA-256 output of this command must be copied into the `source.sha256` field in the `bioconda-recipes/recipes/t1dgrs2/meta.yaml` file.

---

Please follow the steps in the [contributing to the Bioconda package repository](https://bioconda.github.io/contributor/index.html) page for more precise information.
