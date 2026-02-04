#!/usr/bin/env python3
"""
Mediation plot (triangle diagram) for GAVI Regime -> Delivery Strategy -> HPV Coverage.
Based on the logic in exp/socio_mediation_v3.ipynb and exp/mediation.py.
"""

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

from tueplots import bundles, figsizes
from tueplots import cycler
from tueplots.constants.color import palettes


def configure_style(use_tex: bool = False):
    plt.rcParams.update(bundles.icml2024())
    plt.rcParams.update(figsizes.icml2024_half())
    plt.rcParams.update(cycler.cycler(color=palettes.paultol_muted))
    plt.rcParams.update({"text.usetex": bool(use_tex)})


def calculate_model_stats(df, mediator_var):
    results = {}

    contingency = pd.crosstab(df["X"], df[mediator_var])
    chi2, p_a, dof, expected = stats.chi2_contingency(contingency)
    results["a_stat"] = chi2
    results["a_p"] = p_a

    group0 = df[df[mediator_var] == 0]["Y"].values
    group1 = df[df[mediator_var] == 1]["Y"].values
    t_stat, p_b = stats.ttest_ind(group1, group0)
    results["b_stat"] = t_stat
    results["b_p"] = p_b

    gavi_regime_values = df["X"].dropna().unique()
    regime_groups = [df[df["X"] == val]["Y"].values for val in gavi_regime_values]
    f_stat_c, p_c = stats.f_oneway(*regime_groups)
    results["c_stat"] = f_stat_c
    results["c_p"] = p_c

    results["n_total"] = len(df)
    results["regime_means"] = df.groupby("X")["Y"].agg(["mean", "count", "std"]).round(3)
    results["mediator_means"] = df.groupby(mediator_var)["Y"].agg(["mean", "count", "std"]).round(3)
    return results


def draw_mediation(ax, mediator, stats_dict):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    # Paul Tol muted palette (set in configure_style via cycler)
    colors = ["#" + c for c in palettes.paultol_muted]
    fill_X = colors[0]   # rose
    fill_M = colors[1]   # indigo
    fill_Y = colors[2]   # sand
    sig_color = colors[3]   # green
    nonsig_color = "#7f7f7f"
    edge_color = "#222222"
    fill_alpha = 0.22

    X, M, Y = (1.5, 3), (5, 6.5), (8.5, 3)

    for pos, label, fcolor in [
        (X, "GAVI Regime", fill_X),
        (M, mediator, fill_M),
        (Y, "HPV Coverage", fill_Y),
    ]:
        ax.add_patch(
            plt.Rectangle(
                (pos[0] - 1.2, pos[1] - 0.6),
                2.4,
                1.2,
                facecolor=fcolor,
                edgecolor=edge_color,
                alpha=fill_alpha,
                linewidth=1.5,
                zorder=2,
            )
        )
        ax.text(pos[0], pos[1], label, ha="center", va="center", color=edge_color, zorder=3)

    def fmt(stat_val, p, stat_type="chi2"):
        color = sig_color if p < 0.05 else nonsig_color
        weight = "bold" if p < 0.05 else "normal"
        lw = 2 if p < 0.05 else 1

        if stat_type == "chi2":
            label = f"χ² = {stat_val:.2f}"
        elif stat_type == "t":
            label = f"t = {stat_val:.2f}"
        else:
            label = f"F = {stat_val:.2f}"
        return label, color, weight, lw

    a_txt, a_col, a_wt, a_lw = fmt(stats_dict["a_stat"], stats_dict["a_p"], "chi2")
    ax.annotate(
        "",
        xy=(M[0] - 1, M[1] - 0.6),
        xytext=(X[0] + 0.8, X[1] + 0.6),
        arrowprops=dict(arrowstyle="-|>", color=a_col, lw=a_lw),
    )
    ax.text(
        3.0,
        5.9,
        f"Path a\n{a_txt}\np = {stats_dict['a_p']:.3f}",
        color=a_col,
        fontweight=a_wt,
        ha="center",
        va="center",
        linespacing=1.3,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none", alpha=0.8),
    )

    b_txt, b_col, b_wt, b_lw = fmt(stats_dict["b_stat"], stats_dict["b_p"], "t")
    ax.annotate(
        "",
        xy=(Y[0] - 0.8, Y[1] + 0.6),
        xytext=(M[0] + 1, M[1] - 0.6),
        arrowprops=dict(arrowstyle="-|>", color=b_col, lw=b_lw),
    )
    ax.text(
        7.0,
        5.9,
        f"Path b\n{b_txt}\np = {stats_dict['b_p']:.3f}",
        color=b_col,
        fontweight=b_wt,
        ha="center",
        va="center",
        linespacing=1.3,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none", alpha=0.8),
    )

    c_txt, c_col, c_wt, c_lw = fmt(stats_dict["c_stat"], stats_dict["c_p"], "F")
    ax.annotate(
        "",
        xy=(Y[0] - 1.2, Y[1]),
        xytext=(X[0] + 1.2, X[1]),
        arrowprops=dict(arrowstyle="-|>", color=c_col, lw=c_lw, linestyle="--"),
    )
    ax.text(
        5,
        2.2,
        f"Path c'\n{c_txt}\np = {stats_dict['c_p']:.3f}",
        color=c_col,
        fontweight=c_wt,
        ha="center",
        va="center",
        linespacing=1.3,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none", alpha=0.8),
    )


def main():
    parser = argparse.ArgumentParser(description="Mediation triangle plot (2024 data).")
    parser.add_argument(
        "--input",
        type=str,
        default=str(Path(__file__).resolve().parent.parent.parent / "dataset_country_analysis_with_gavi_trajectory.xlsx"),
        help="Path to dataset_country_analysis_with_gavi_trajectory.xlsx",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=str(Path(__file__).resolve().parent.parent.parent / "fig"),
        help="Output directory for figures",
    )
    parser.add_argument("--no_tex", action="store_true", help="Disable LaTeX text rendering")
    args = parser.parse_args()

    configure_style(use_tex=not args.no_tex)

    df_all = pd.read_excel(args.input, sheet_name="Sheet1", engine="openpyxl")
    df = df_all[df_all["year"] == 2024].copy()

    req = ["type_prim_deliv_vax", "HPV_INT_DOSES", "gavi_regime_it", "vax_fd_cov", "income_class"]
    df2 = df.dropna(subset=req).copy()

    df_analysis = df2.copy()
    df_analysis["X"] = df_analysis["gavi_regime_it"]
    df_analysis["Y"] = df_analysis["vax_fd_cov"]

    df_analysis["type_prim_deliv_vax"] = df_analysis["type_prim_deliv_vax"].replace(
        {"School.based": "School-based", "Facility based": "Facility-based"}
    )
    df_analysis["M"] = (df_analysis["type_prim_deliv_vax"] == "School-based").astype(int)
    df_analysis = df_analysis[df_analysis["M"].notna()].copy()

    stats_dict = calculate_model_stats(df_analysis, "M")

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    draw_mediation(ax, "Delivery Strategy", stats_dict)
    ax.set_title("Delivery Strategy as Mediator (School-based vs Non-school-based)", pad=30)

    # Note removed; add in LaTeX instead.

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_pdf = outdir / "mediation_icml.pdf"
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.02)
    print(f"Saved PDF: {out_pdf}")
    plt.close(fig)


if __name__ == "__main__":
    main()
