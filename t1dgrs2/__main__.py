#!/usr/bin/env python3

import os
from sys import exit
from yaml import safe_load
from logging import getLogger
from argparse import ArgumentParser

from t1dgrs2 import common, score, metrics, _EXIT_MSG, __version__

_LOG = getLogger(__name__)


def main(plink_bfile: str, config_file: str, plink_out: str) -> None:
    """Main method to generate a T1DGRS2.

    Args:
        - plink_bfile (str) : PLINK --bfile argument value.
        - config_file (str) : Path to the configuration file containing required variables for script execution.
        - plink_out (str) : PLINK --out argument value. Defaults to './output'.
    """
    _LOG.debug(
        f"Running main(plink_bfile='{plink_bfile}', config_file='{config_file}', plink_out='{plink_out}')"
    )
    try:
        with open(config_file, mode="r", encoding="UTF-8") as f:
            config = safe_load(f)
        plink_out_check = True if os.sep in plink_out else False
        if plink_out_check:
            os.makedirs(os.path.dirname(plink_out), exist_ok=True)
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        exit(1)

    df_vmap = score.fix_variant_alleles(
        rdqfile=os.path.realpath(config["input"]["dq_rank"]),
        bfile=plink_bfile,
        ofile=plink_out,
        mfile=os.path.realpath(config["input"]["hla_map"]),
    )
    df_vmap.attrs["name"] = "Mapping & frequency data"
    df_dosage = score.create_dosage_table(
        df_vmap=df_vmap, bfile=plink_bfile, ofile=plink_out
    )
    df_dosage.attrs["name"] = "Dosage data for all mapped alleles"
    dosage_file = os.path.realpath(f"{plink_out}_dosage.tsv")
    _LOG.info(f"Writing dosage data to '{dosage_file}'")
    df_dosage.to_csv(
        dosage_file, sep="\t", na_rep="", header=True, index=False, encoding="UTF-8"
    )
    df_geno = score.get_geno_call_alleles(
        df_dsg=df_dosage, alleles=df_vmap["ALLELE"].to_list()
    )
    df_geno.attrs["name"] = "Genotype calls for all mapped alleles"
    geno_file = os.path.realpath(f"{plink_out}_DQ_calls.tsv")
    _LOG.info(f"Writing DQ calls data to '{geno_file}'")
    df_geno.to_csv(
        geno_file, sep="\t", na_rep="", header=True, index=False, encoding="UTF-8"
    )
    df_scores = score.generate_grs(
        df_geno=df_geno,
        bfile=plink_bfile,
        ofile=plink_out,
        rdqfile=os.path.realpath(config["input"]["dq_rank"]),
        sc_int=os.path.realpath(config["scores"]["interaction"]),
        sc_plink_all=os.path.realpath(config["scores"]["all_variants"]),
        sc_plink_hla=os.path.realpath(config["scores"]["hla_variants"])
        if "hla_variants" in config["scores"].keys()
        else "",
    )
    df_scores.attrs["name"] = "Calculated GRS for all given variants"

    if "metrics" in config:
        df_scores = metrics.retrieve_centiles(
            df_scores=df_scores,
            rfile=os.path.realpath(config["metrics"]["centiles_file"]),
        )
        df_scores.attrs[
            "name"
        ] = "Calculated GRS, centiles and PPV for all given variants"
        df_scores = metrics.calculate_probs(
            df_scores=df_scores,
            ffile=os.path.realpath(config["metrics"]["params_file"]),
        )
        df_scores.attrs[
            "name"
        ] = "Calculated GRS, centiles, PPV and probability for all given variants"

    results_file = os.path.realpath(f"{plink_out}_RESULTS.tsv")
    _LOG.info(f"Writing results to '{results_file}'")
    df_scores.to_csv(
        results_file, sep="\t", na_rep="", header=True, index=False, encoding="UTF-8"
    )


if __name__ == "__main__":
    _LOG.info(f"Started module execution: '{__package__}'")
    parser = ArgumentParser(
        prog=f"python -m {__package__}",
        description="Generate a T1D GRS accounting for HLA-DQ interaction terms.",
    )
    parser.add_argument(
        "-b",
        "--bfile",
        dest="plink_bfile",
        metavar="BFILE",
        required=True,
        type=common.validate_plinkfiles,
        help="PLINK --bfile prefix (bed/bim/fam file path & name without extension).",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        metavar="CONFIG",
        required=True,
        type=common.validate_textfile,
        help="Path to the T1DGRS2 configuration file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="plink_out",
        metavar="OUTPUT",
        default=f"{os.getcwd()}/output",
        help="PLINK --out prefix (output file path & name, defaults to './output').",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="check_list_variants",
        help="List the T1DGRS2 input variants and exit.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        help="Show the conda-prefix-replacement package version number and exit.",
        version="%(prog)s : " + __version__,
    )
    args = parser.parse_args()
    try:
        if args.check_list_variants:
            common.list_variants(config_file=args.config_file)
        else:
            main(
                plink_bfile=args.plink_bfile,
                config_file=args.config_file,
                plink_out=args.plink_out,
            )
    except Exception as e:
        _LOG.exception(e)
        _LOG.error(_EXIT_MSG)
        exit(1)
    finally:
        _LOG.info(f"Completed module execution: '{__package__}'")
