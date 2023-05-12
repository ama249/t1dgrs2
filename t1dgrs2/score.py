#!/usr/bin/env python3

"""Module containing the core logic for generating the T1DGRS2.

This module contains the core methods to calculate allelic dosage, convert 
the dosage to genotype hard calls, then compute the T1DGRS2 taking into account 
HLA-DQ interaction scoring data.

Methods:
    - fix_variant_alleles : Reconcile mapping data from the configuration 
    with the --freq report of the given PLINK --bfile.
    - create_dosage_table : Calculate per individual allele dosage from the mapping data.
    - get_geno_call_alleles : Obtain DQ allele names from per individual genotype counts.
    - generate_grs : Calculate the T1DGRS2 from the given PLINK --bfile, DQ allele 
    genotype calls, and all relevant scoring data.
"""

# Standard imports
import os as _os
import re as _re
import pandas as _pd
from sys import exit as _exit
from numpy import arange as _arange
from logging import getLogger as _getLogger
from numpy import rint as _rint, ubyte as _UBYTE

# Module imports
from . import common as _common, _EXIT_MSG

_LOG = _getLogger(__name__)


def _apply_fix_variant_alleles(row: _pd.Series) -> _pd.Series | None:
    """For each variant in the mapping data, determine the final score allele.

    Args:
        - row (pandas.Series) : Row from the mapping DataFrame with the 
        required variant details.

    Returns:
        pandas.Series | None : Row containing the final score allele for that variant.
    """
    if _pd.isna(row["A1_freq"]) or row["A1_map"] in [row["A1_freq"], row["A2"]]:
        return row["A1_map"]
    # score allele is shorter indel sequence but there is no data for longer one
    elif row["A1_map"] == "-" and row["A1_freq"] == "0" and len(row["A2"]) == 1:
        # score allele must be F2
        return row["A2"]
    # score allele is longer indel sequence and corresponds to F2
    elif len(row["A2"]) > len(row["A1_map"]) > 1:
        # score allele must be F2 whether have F1 or not
        return row["A2"]
    # score allele is longer indel sequence and corresponds to F1
    elif len(row["A1_map"]) > 1 and len(row["A2"]) == 1:
        if row["A2"] == "-":
            return row["A1_map"]
        elif row["A1_freq"] == "0":
            return row["A2"] + row["A1_map"]
        else:
            return row["A1_freq"]
    # other standard missing allele cases
    elif row["A1_map"] != "-" and row["A1_freq"] == "0":
        return row["A1_map"]
    # other standard missing allele cases
    elif row["A1_map"] == "-" and row["A1_freq"] != "0":
        # score allele must be shorter of F1 and F2
        return min(row["A1_freq"], row["A2"], key=len)
    # remaining cases - score allele is shorter indel sequence and corresponds to F1
    # score allele is missing - since can never score leave as "-"
    elif row["A1_map"] == "-" and row["A1_freq"] == "0":
        return row["A1_map"]
    else:
        return None


def _apply_get_geno_call_alleles(row: _pd.Series, max_calls: int) -> list[str]:
    """For each DQ allele genotype count per individual, calculate the 
    first N rank-ordered DQ allele names (with or without repetition).

    Args:
        - row (pandas.Series) : Row from the dosage DataFrame, with the 
        rank-ordered DQ alleles as column names and the genotype counts as values.
        - max_calls (int) : Maximum number of DQ allele calls considered 
        per individual (excess calls are truncated).

    Returns:
        list[str] : List with the first N DQ allele names per individual 
        (right-padded with 'X' for empty calls), where 2 <= N <= max_calls.
    """
    data = row.loc[row > 0]
    data_serialise = [
        [allele] * freq for allele, freq in dict(zip(data.index, data.values)).items()
    ]
    data_serialise_flat = [item for sublist in data_serialise for item in sublist]
    data_serialise_flat_fill = sum([data_serialise_flat, ["X"] * max_calls], [])[
        :max_calls
    ]
    return data_serialise_flat_fill


def fix_variant_alleles(
    rdqfile: str, bfile: str, ofile: str, mfile: str
) -> _pd.DataFrame:
    """Reconcile mapping data from the configuration with the --freq 
    report of the given PLINK --bfile.

    Args:
        - rdqfile (str) : Path to the DQ allele ranking file from the configuration.
        - bfile (str) : PLINK --bfile argument value.
        - ofile (str) : PLINK --out argument value.
        - mfile (str) : Path to the mapping file containing the DQ allele name, 
        variant ID, and score allele.

    Returns:
        pandas.DataFrame : Contains the combination of both mapping and frequency data.
    """
    _LOG.debug(
        f"Executing: fix_variant_alleles("
        + f"rdqfile='{rdqfile}', "
        + f"bfile='{bfile}', "
        + f"ofile='{ofile}', "
        + f"mfile='{mfile}')"
    )
    _LOG.info("Generating PLINK frequency report")
    ofile_dir: str = _os.path.dirname(ofile)
    ofile_name: str = _os.path.basename(ofile)
    temp_path: str = f"{ofile_dir}/temp_{ofile_name}"
    command = f"plink --bfile '{bfile}' --freq --out '{temp_path}'"
    _: str = _common.run_shell_cmd(cmd=command)  # return value not used here
    try:
        df_rdq: _pd.DataFrame = _pd.read_csv(rdqfile, sep="\t", usecols=["DQ", "RANK"])
        df_freq: _pd.DataFrame = _pd.read_csv(
            f"{temp_path}.frq",
            sep="\s+",
            usecols=["CHR", "SNP", "A1", "A2", "MAF", "NCHROBS"],
        )
        df_freq.attrs["name"] = "PLINK --freq output"
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    _LOG.info("Combining mapping file data with frequency report data")
    try:
        df_map: _pd.DataFrame = _pd.read_csv(
            mfile, sep="\t", usecols=["ALLELE", "SNP", "A1"]
        )
        df_map.attrs["name"] = "Mapping file containing score allele"
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    df_vmap: _pd.DataFrame = df_map.merge(
        df_freq, how="left", on="SNP", suffixes=("_map", "_freq")
    )
    df_vmap["A1"] = df_vmap.apply(_apply_fix_variant_alleles, axis=1)
    _LOG.info("Sorting mapped variants by DQ rank order")
    df_vmap = (
        df_vmap.merge(df_rdq, how="left", left_on="ALLELE", right_on="DQ")
        .drop(columns=["DQ"])
        .sort_values(by=["RANK"])
        .reset_index(drop=True)
    )
    return df_vmap


def create_dosage_table(
    df_vmap: _pd.DataFrame, bfile: str, ofile: str
) -> _pd.DataFrame:
    """Calculate per individual allele dosage from the mapping data.

    Args:
        - df_vmap (pandas.DataFrame) : Contains the rank-ordered mapping data.
        - bfile (str) : PLINK --bfile argument value.
        - ofile (str) : PLINK --out argument value.

    Returns:
        pandas.DataFrame : Contains the per individual allelic dosage values.
    """
    _LOG.debug(
        f"Executing: create_dosage_table("
            + f"""df_vmap='{df_vmap.attrs["name"]}', """
            + f"""bfile='{bfile}', ofile='{ofile}')"""
    )
    _LOG.info("Creating dosage table based on data from mapping & frequency report")
    ofile_dir: str = _os.path.dirname(ofile)
    ofile_name: str = _os.path.basename(ofile)
    temp_path: str = f"{ofile_dir}/temp_{ofile_name}"
    df_scores: _pd.DataFrame = df_vmap[["SNP", "A1"]].copy(deep=True)
    df_scores["VAL"] = 1
    df_rngqty: _pd.DataFrame = df_vmap[["SNP", "RANK"]].copy(deep=True)
    df_rngbound: _pd.DataFrame = df_rngqty.copy(deep=True)
    df_rngbound["LOW"], df_rngbound["HIGH"] = (
        df_rngbound["RANK"] - 0.5,
        df_rngbound["RANK"] + 0.5,
    )
    df_rngbound.drop(columns=["RANK"], inplace=True)
    try:
        df_scores.to_csv(
            f"{temp_path}.scores", sep="\t", index=False, header=False, encoding="UTF-8"
        )
        df_rngqty.to_csv(
            f"{temp_path}.rngqty", sep="\t", index=False, header=False, encoding="UTF-8"
        )
        df_rngbound.to_csv(
            f"{temp_path}.rngbound",
            sep="\t",
            index=False,
            header=False,
            encoding="UTF-8",
        )
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    command: str = (
        f"plink --bfile '{bfile}' --score '{temp_path}.scores' no-mean-imputation "
        + f"--q-score-range '{temp_path}.rngbound' '{temp_path}.rngqty' --out '{temp_path}'"
    )
    _: str = _common.run_shell_cmd(cmd=command)  # return value not used here
    qscore_file_rgx: _re.Pattern[str] = _re.compile(f"{temp_path}\.(\S+)\.profile$")
    qscore_alleles_map: dict[str, str] = {}
    for r, _, fs in _os.walk(ofile_dir):
        for f in fs:
            qscore_file: str = _os.path.join(r, f)
            m: _re.Match[str] | None = _re.search(qscore_file_rgx, qscore_file)
            if m is not None:
                qscore_alleles_map[
                    df_vmap.loc[df_vmap["SNP"] == m.group(1), "ALLELE"].item()
                ] = qscore_file
    _LOG.info(
        "Concatenating range score profiles for each mapping DQ allele "
            + "into a single table"
    )
    df_dosage: _pd.DataFrame = None
    try:
        for qscore_allele, qscore_file in qscore_alleles_map.items():
            if df_dosage is None:
                df_dosage: _pd.DataFrame = _pd.read_csv(
                    qscore_file,
                    sep="\s+",
                    usecols=["FID", "IID", "SCORE"],
                    dtype={"FID": str, "IID": str},
                )
                df_dosage.rename(columns={"SCORE": qscore_allele}, inplace=True)
            else:
                df_dosage_temp: _pd.DataFrame = _pd.read_csv(
                    qscore_file,
                    sep="\s+",
                    usecols=["FID", "IID", "SCORE"],
                    dtype={"FID": str, "IID": str},
                )
                df_dosage_temp.rename(columns={"SCORE": qscore_allele}, inplace=True)
                df_dosage = df_dosage.merge(
                    df_dosage_temp, how="outer", on=["FID", "IID"]
                )
                del df_dosage_temp
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    vmap_alleles: list[str] = df_vmap["ALLELE"].to_list()
    qscore_alleles: list[str] = list(qscore_alleles_map.keys())
    # Get elements present in vmap_alleles but not in qscore_alleles, 
    # i.e., list(vmap_alleles) - list(qscore_alleles)
    no_qscore_alleles: list[str] = list(
        set(vmap_alleles).difference(set(qscore_alleles))
    )
    _LOG.info("Converting dosage data to genotype data")
    df_dosage[no_qscore_alleles] = 0.0
    df_dosage = df_dosage[["FID", "IID"] + vmap_alleles]
    df_dosage[vmap_alleles] = _rint(df_dosage[vmap_alleles] * 2).astype(_UBYTE)
    _common.delete_files_within(dirpath=ofile_dir, pattern=temp_path)
    return df_dosage


def get_geno_call_alleles(
    df_dsg: _pd.DataFrame, alleles: list[str], max_calls: int = 2
) -> _pd.DataFrame:
    """Obtain DQ allele names from per individual genotype counts.

    Args:
        - df_dsg (pandas.DataFrame) : Dosage data containing per individual 
        and per DQ allele genotype counts.
        - alleles (list[str]) : List of rank-ordered DQ allele names, 
        taken from mapping file.
        - max_calls (int, optional) : Maximum number of DQ allele calls 
        to consider per individual. Requires max_calls >= 2 (default).

    Returns:
        pandas.DataFrame : Contains the DQ allele calls per individual 
        (with or without repetition).
    """
    max_calls = 2
    _LOG.debug(
        "Executing: get_geno_call_alleles(" + \
        f"""df_dsg='{df_dsg.attrs["name"]}', """ + \
        f"""alleles={alleles}, max_calls={max_calls})"""
    )
    _LOG.info("Retrieving genotype calls for mapping alleles")
    df_geno: _pd.DataFrame = df_dsg[["FID", "IID"]].copy(deep=True)
    # max_calls = df_dsg[alleles].max(axis=0).max()
    df_geno["CALLS"] = df_dsg[alleles].apply(
        _apply_get_geno_call_alleles, max_calls=max_calls, axis=1
    )
    df_geno[["GENO1", "GENO2"]] = _pd.DataFrame(
        df_geno["CALLS"].tolist(), index=df_geno.index
    )
    return df_geno


def generate_grs(
    df_geno: _pd.DataFrame,
    bfile: str,
    ofile: str,
    rdqfile: str,
    sc_int: str,
    sc_plink: str,
    sc_dq_plink: str = "",
) -> _pd.DataFrame:
    """Calculate the T1DGRS2 from the given PLINK --bfile, DQ allele 
    genotype calls, and all relevant scoring data.

    Args:
        - df_geno (pandas.DataFrame) : Contains the DQ allele genotype calls.
        - bfile (str) : PLINK --bfile argument value.
        - ofile (str) : PLINK --out argument value.
        - rdqfile (str) : Path to the DQ allele ranking file from the configuration.
        - sc_int (str) : Path to the DQ allele interaction score file 
        from the configuration.
        - sc_plink (str) : Path to the linear score file for all variants 
        from the configuration.
        - sc_dq_plink (str, optional) : Path to the linear score file for only 
        the DQ allele variants. Will not be included in the final calculation 
        if empty string (default).

    Returns:
        pandas.DataFrame : Contains the per individual T1DGRS2 values.
    """
    _LOG.debug(
        "Executing: generate_grs("
            + f"""df_geno='{df_geno.attrs["name"]}', """
            + f"""bfile='{bfile}', """
            + f"""ofile='{ofile}', """
            + f"""rdqfile='{rdqfile}', """
            + f"""sc_int='{sc_int}', """
            + f"""sc_plink='{sc_plink}', """
            + f"""sc_dq_plink='{sc_dq_plink}')"""
    )
    ofile_dir: str = _os.path.dirname(ofile)
    ofile_name: str = _os.path.basename(ofile)
    temp_path: str = f"{ofile_dir}/temp_{ofile_name}"
    try:
        df_rdq: _pd.DataFrame = _pd.read_csv(
            rdqfile, sep="\t", usecols=["DQ", "RANK"]
        )
        df_sc_int: _pd.DataFrame = _pd.read_csv(
            sc_int, sep="\t", usecols=["ALLELE1", "ALLELE2", "BETA"]
        )
        df_sc_int.attrs["name"] = "Mapped DQ allele variants interaction scores"
        df_sc_plink: _pd.DataFrame = _pd.read_csv(
            sc_plink, sep="\t", usecols=["ID", "ALLELE", "BETA"]
        )
        df_sc_plink.attrs["name"] = "All variants PLINK scores"
        df_sc_dq_plink: _pd.DataFrame = _pd.read_csv(
            sc_dq_plink, sep="\t", usecols=["ID", "ALLELE", "BETA"]
        )
        df_sc_dq_plink.attrs["name"] = "Mapped DQ allele variants PLINK scores"
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    _LOG.info("Retrieving scores for interacting DQ alleles")
    allele_cols = sorted(
        df_sc_int.columns[df_sc_int.columns.str.startswith("ALLELE")].to_list()
    )
    geno_cols = sorted(
        df_geno.columns[df_geno.columns.str.startswith("GENO")].to_list()
    )
    # Operations to rank-order DQ allele interations from the interactions score file
    df_sc_int["SNO"] = _arange(
        start=1, stop=len(df_sc_int.index) + 1, step=1, dtype=int
    )
    df_sc_int_long = df_sc_int.melt(
        id_vars=["SNO"], value_vars=allele_cols
    ).reset_index(drop=True)
    df_sc_int_long = (
        df_sc_int_long.merge(df_rdq, how="left", left_on="value", right_on="DQ")
        .sort_values(by=["SNO", "RANK"])
        .reset_index(drop=True)
    )
    df_sc_int_long["ALLELE_ORDER"] = (
        df_sc_int_long.groupby(by=["SNO"])["RANK"]
        .transform("rank", method="first")
        .astype(int)
    )
    df_sc_int_long["ALLELE_ORDER"] = \
        "ALLELE" + df_sc_int_long["ALLELE_ORDER"].astype(str)
    df_sc_int_mod = df_sc_int_long.pivot(
        index=["SNO"], columns=["ALLELE_ORDER"], values=["value"]
    ).reset_index()
    df_sc_int_mod.columns = df_sc_int_mod.columns.droplevel(0)
    df_sc_int_mod.columns.name = None
    df_sc_int_mod.rename(columns={"": "SNO"}, inplace=True)
    df_sc_int = (
        df_sc_int_mod.merge(df_sc_int[["SNO", "BETA"]], how="inner", on="SNO")
        .drop(columns=["SNO"])
        .reset_index(drop=True)
    )
    del df_sc_int_long, df_sc_int_mod
    df_scores: _pd.DataFrame = (
        df_geno[["FID", "IID"] + geno_cols]
        .merge(df_sc_int, how="left", left_on=geno_cols, right_on=allele_cols)
        .drop(columns=geno_cols + allele_cols)
        .fillna({"BETA": 0})
        .reset_index(drop=True)
    )
    _LOG.info("Computing SCORE based on interaction terms & weights for all variants")
    command: str = (
        f"plink --bfile '{bfile}' --score '{sc_plink}' 'header' sum --out '{temp_path}'"
    )
    _common.run_shell_cmd(cmd=command)
    try:
        df_sc_plink_calc = _pd.read_csv(
            f"{temp_path}.profile",
            sep="\s+",
            usecols=["FID", "IID", "SCORESUM"],
            dtype={"FID": str, "IID": str},
        )
        df_sc_plink_calc.rename(columns={"SCORESUM": "SCORESUM_plink"}, inplace=True)
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    df_scores = df_scores.merge(
        df_sc_plink_calc, how="inner", on=["FID", "IID"]
    ).reset_index(drop=True)
    df_scores["SCORE"] = df_scores[["BETA", "SCORESUM_plink"]].sum(axis=1)
    if sc_dq_plink != "":
        _LOG.info(
            "Computing DQSCORE based on interaction terms & weights for DQ allele variants"
        )
        command: str = (
            f"plink --bfile '{bfile}' --score '{sc_dq_plink}' 'header' "
                + f"sum --out '{temp_path}_dq'"
        )
        _common.run_shell_cmd(cmd=command)
        try:
            df_sc_dq_plink_calc = _pd.read_csv(
                f"{temp_path}_dq.profile",
                sep="\s+",
                usecols=["FID", "IID", "SCORESUM"],
                dtype={"FID": str, "IID": str},
            )
            df_sc_dq_plink_calc.rename(
                columns={"SCORESUM": "SCORESUM_dq_plink"}, inplace=True
            )
        except Exception as e:
            _LOG.exception(e)
            _LOG.error(_EXIT_MSG)
            _exit(1)
        df_scores = df_scores.merge(
            df_sc_dq_plink_calc,
            how="inner",
            on=["FID", "IID"],
        ).reset_index(drop=True)
        df_scores["DQSCORE"] = df_scores[["BETA", "SCORESUM_dq_plink"]].sum(axis=1)
    score_cols_to_drop = sum(
        [["BETA"], [col for col in df_scores.columns if col.startswith("SCORESUM")]], []
    )
    df_scores.drop(columns=score_cols_to_drop, inplace=True)
    _common.delete_files_within(dirpath=ofile_dir, pattern=temp_path)
    return df_scores
