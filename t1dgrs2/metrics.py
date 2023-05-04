#!/usr/bin/env python3

# Standard imports
import pandas as _pd
from sys import exit as _exit
from logging import getLogger as _getLogger
from numpy import exp as _exp, nan as _NAN

# Module imports
from . import _EXIT_MSG

_LOG = _getLogger(__name__)


def retrieve_centiles(df_scores: _pd.DataFrame, rfile: str) -> _pd.DataFrame:
    """Retrieve and assign pre-computed control/case centile values for each individual with a calculated T1DGRS2.

    Args:
        - df_scores (pandas.DataFrame) : Contains the calculated T1DGRS2 values.
        - rfile (str) : Path to the ROC curve file containing control/case centiles and PPV data.

    Returns:
        pandas.DataFrame : Updated with control/case centiles and PPV values per individual.
    """
    _LOG.debug(
        f"""Executing: retrieve_centiles(df_scores='{df_scores.attrs["name"]}', rfile: str)"""
    )
    _LOG.info(
        "Retrieving and assigning pre-computed control/case centiles per individual T1DGRS2"
    )
    try:
        df_roc: _pd.DataFrame = _pd.read_csv(
            rfile,
            sep="\t",
            usecols=["threshold", "CtrlPCentile", "CasePCentile", "PPV"],
        )
        df_roc.attrs["name"] = "Pre-computed ROC curve threshold and metric values"
        df_roc.rename(
            columns={"CtrlPCentile": "CTRLCENTILE", "CasePCentile": "CASECENTILE"},
            inplace=True,
        )
        df_roc["SOURCE"] = "ROCFILE"
        df_scores["SOURCE"] = "SCOREFILE"
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    df_roc_temp: _pd.DataFrame = (
        df_roc[["threshold", "SOURCE"]]
        .copy(deep=True)
        .rename(columns={"threshold": "SCORE"})
    )
    df_roc_temp[["FID", "IID"]] = _pd.DataFrame(columns=["FID", "IID"], dtype="str")
    df_roc_temp["DQSCORE"] = _NAN
    df_roc_temp = df_roc_temp[["SOURCE", "FID", "IID", "SCORE", "DQSCORE"]]
    df_scores_temp: _pd.DataFrame = df_scores[
        ["SOURCE", "FID", "IID", "SCORE", "DQSCORE"]
    ].copy(deep=True)
    df_scores_upd: _pd.DataFrame = (
        _pd.concat([df_roc_temp, df_scores_temp])
        .sort_values(by=["SCORE"])
        .reset_index(drop=True)
    )
    del df_scores_temp, df_roc_temp
    # Merging on the SOURCE column ensures that only the df_roc data rows are updated
    df_scores_upd = df_scores_upd.merge(
        df_roc,
        how="left",
        left_on=["SOURCE", "SCORE"],
        right_on=["SOURCE", "threshold"],
    )
    # Combination of nearest interpolation, back-fill & forward-fill assigns all individuals their respective centile values
    # IMPORTANT: SPLINE INTERPOLATION THEORETICALLY BETTER, TO BE TESTED
    df_scores_upd = df_scores_upd.interpolate(method="nearest").bfill().ffill()
    # Remove all the df_roc intermediate data rows
    df_scores_upd = (
        df_scores_upd.drop(df_scores_upd.loc[df_scores_upd["SOURCE"] == "ROC"].index)
        .loc[
            df_scores_upd["SOURCE"] == "SCOREFILE",
            ["FID", "IID", "SCORE", "DQSCORE", "CTRLCENTILE", "CASECENTILE", "PPV"],
        ]
        .sort_values(by=["FID", "IID"])
        .reset_index(drop=True)
    )
    return df_scores_upd


def calculate_probs(df_scores: _pd.DataFrame, ffile: str) -> _pd.DataFrame:
    """Calculate the probability of individual being classified as a case, using pre-computed two-sample t-test statistics.

    Args:
        - df_scores (pandas.DataFrame) : Contains the per individual T1DGRS2 scores.
        - ffile (str) : Path to the two-sample t-test statistics file.

    Returns:
        pandas.DataFrame : Updated with the per individual probabilities of being classified as a case.
    """
    _LOG.debug(
        f"""Executing: calculate_probs(df_scores='{df_scores.attrs["name"]}', ffile: str)"""
    )
    _LOG.info(
        "Calculating the case probability per individual based on pre-computed two-sample t-test statistics"
    )
    try:
        df_fit: _pd.DataFrame = _pd.read_csv(
            ffile,
            sep="\t",
            usecols=["Param", "Estimate", "Std_Error", "t_value", "Pr_gt_t"],
        )
        df_fit.attrs["name"] = "Pre-computed two-sample t-test mid and b estimates"
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        _exit(1)
    b = df_fit.loc[df_fit["Param"] == "b", "Estimate"].item()
    mid = df_fit.loc[df_fit["Param"] == "mid", "Estimate"].item()
    df_scores["PROB"] = 1.0 / (1.0 + _exp(b * (mid - df_scores["SCORE"])))
    return df_scores
