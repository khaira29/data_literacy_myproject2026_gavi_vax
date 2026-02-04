#!/usr/bin/env python3
# ============================================================
# gavi_analysis_3_own_split.py
#
# Figure 3: Raw mean vs model-predicted trajectories (NON-HIC only),
# split into TWO separate figures for readability:
#   - Figure 3a: 2015–2019
#   - Figure 3b: 2020–2024 (with COVID shading + 2022 dashed line)
#
# Outputs:
#   - PDF (vector) always
#   - PNG preview optional
#   - Excel tables: raw means + predicted grid
# ============================================================

from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from scipy.stats import norm

from tueplots import bundles, figsizes


def configure_style(use_tex: bool = False, full_width: bool = True):
    plt.rcParams.update(bundles.icml2024())
    plt.rcParams.update(figsizes.icml2024_full() if full_width else figsizes.icml2024_half())
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.alpha": 0.25,
            "legend.frameon": True,
            "legend.framealpha": 0.90,
        }
    )
    if use_tex:
        plt.rcParams.update(
            {
                "text.usetex": True,
                "font.family": "serif",
                "font.serif": ["Times", "TeX Gyre Termes", "Nimbus Roman", "DejaVu Serif"],
            }
        )
    else:
        plt.rcParams.update({"text.usetex": False})


def make_plot(
    outpath_pdf: Path,
    outpath_png,
    years: list[int],
    raw_means: pd.DataFrame,
    pred_df: pd.DataFrame,
    trajectories: list[str],
    trajectory_label_map: dict,
    colors: dict,
    show_covid: bool = False,
    show_2022: bool = False,
    legend: bool = True,
):
    fig, ax = plt.subplots(constrained_layout=True)

    # Optional shading / markers
    if show_covid:
        ax.axvspan(2020, 2021, color="#D55E00", alpha=0.10, zorder=0)
        ax.text(
            2020.5, 0.98, "COVID-19",
            transform=ax.get_xaxis_transform(),
            ha="center", va="top",
            fontsize=8,
            color="#D55E00",
            alpha=0.9,
        )

    if show_2022:
        ax.axvline(
            2022,
            color="#E377C2",   # pink"
            linestyle="-",
            linewidth=1.2,
            alpha=0.9,
        )

        ax.text(
            2022, 0.96,
            "Gavi MIC entry",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=4.0,
            color="#E377C2",
        )


    # Raw vs model styles
    model_kwargs = dict(
        linestyle="-",
        linewidth=1.3,     
        alpha=0.9,
    )
    raw_kwargs = dict(
        linestyle="--",
        linewidth=0.6,    
        marker="o",
        markersize=2.0,    
        markerfacecolor="none",
        alpha=0.30,
    )


    # Plot each group
    for g in trajectories:
        pretty = trajectory_label_map.get(g, g)
        c = colors.get(g, None)

        sub_raw = raw_means[raw_means["gavi_trajectory"] == g].sort_values("year")
        sub_pred = pred_df[pred_df["gavi_trajectory"] == g].sort_values("year")

        # Restrict to years range
        sub_raw = sub_raw[sub_raw["year"].isin(years)]
        sub_pred = sub_pred[sub_pred["year"].isin(years)]

        # Raw (dashed)
        ax.plot(
            sub_raw["year"], sub_raw["raw_mean"],
            color=c,
            label=pretty,
            **raw_kwargs,
        )
        # Model (solid)
        ax.plot(
            sub_pred["year"], sub_pred["pred_mean"],
            color=c,
            **model_kwargs,
        )

    # Axes
    ax.set_xlim(min(years), max(years))
    ax.set_xticks(years)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Year")
    ax.set_ylabel(
        "Model-predicted HPV vax\nfirst-dose coverage (%)",
        fontsize=6,
        labelpad=4
    )
    ax.grid(True, axis="y")
    ax.grid(False, axis="x")

    # Small in-plot note
    # Small in-plot note (upper right)
    ax.text(
        0.98, 0.02,
        "Dashed = raw mean | Solid = model",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.0,
        alpha=0.8,
    )


    # Small legend (ONLY groups)
    if legend:
        leg = ax.legend(
            title="Gavi status",
            loc="upper right",
            fontsize=3.0,
            title_fontsize=4.0,
            handlelength=1.2,
            handletextpad=0.4,
            labelspacing=0.20,
            borderpad=0.25,
        )
        leg.get_frame().set_alpha(0.9)

    ax.set_title("")

    fig.savefig(outpath_pdf, bbox_inches="tight", pad_inches=0.02, transparent=True)
    print(f"Saved PDF: {outpath_pdf}")
    if outpath_png is not None:
        fig.savefig(outpath_png, dpi=300, bbox_inches="tight", pad_inches=0.02, transparent=True)
        print(f"Saved PNG: {outpath_png}")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Generate Figure 3 split (2015–2019, 2020–2024).")
    parser.add_argument("--input", type=str, required=True, help="Path to dataset_country_analysis_with_gavi_trajectory.xlsx")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory for figures and tables")
    parser.add_argument("--png", action="store_true", help="Also save PNG previews")
    parser.add_argument("--no_tex", action="store_true", help="Disable LaTeX text rendering (recommended on macOS).")
    parser.add_argument("--half", action="store_true", help="Use half-column width (default full width).")
    args = parser.parse_args()

    configure_style(use_tex=not args.no_tex, full_width=not args.half)
    plt.rcParams.update({
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 6.5,
    "legend.title_fontsize": 6.5,   
    })


    input_xlsx = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_raw = outdir / "Table_Figure3_raw_means_by_year_trajectory_NONHIC_2015_2024.xlsx"
    out_pred = outdir / "Table_Figure3_model_predicted_means_by_year_trajectory_NONHIC_2015_2024.xlsx"

    out_pdf_a = outdir / "Figure3a_raw_vs_model_predicted_trajectories_NONHIC_2015_2019.pdf"
    out_pdf_b = outdir / "Figure3b_raw_vs_model_predicted_trajectories_NONHIC_2020_2024.pdf"

    out_png_a = outdir / "Figure3a_raw_vs_model_predicted_trajectories_NONHIC_2015_2019.png"
    out_png_b = outdir / "Figure3b_raw_vs_model_predicted_trajectories_NONHIC_2020_2024.png"

    # ------------------------------------------------------------
    # Load + prepare data
    # ------------------------------------------------------------
    df = pd.read_excel(input_xlsx, engine="openpyxl")

    required = {"country_code", "year", "income_class", "vax_fd_cov", "gavi_trajectory"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)

    df["income_class"] = df["income_class"].astype("string").str.strip().str.upper()
    df["vax_fd_cov"] = pd.to_numeric(df["vax_fd_cov"], errors="coerce")
    df["gavi_trajectory"] = df["gavi_trajectory"].astype("string").str.strip()

    df = df[df["year"].between(2015, 2024)].copy()
    df = df.dropna(subset=["country_code", "income_class", "vax_fd_cov", "gavi_trajectory"]).copy()
    df = df[df["income_class"] != "H"].copy()

    df["time"] = df["year"] - 2015

    # ------------------------------------------------------------
    # Labels, order, colors
    # ------------------------------------------------------------
    trajectory_order = [
        "Classic Gavi (always)",
        "Classic → MIC (graduated)",
        "Never → MIC (MICs entry)",
        "Never Gavi (always)",
    ]
    trajectory_label_map = {
        "Classic Gavi (always)": "Gavi-supported",
        "Classic → MIC (graduated)": "Former-Gavi MIC",
        "Never → MIC (MICs entry)": "New-Gavi MIC",
        "Never Gavi (always)": "Never-Gavi non-HIC",
    }
    COLORS = {
        "Classic Gavi (always)": "#0072B2",
        "Classic → MIC (graduated)": "#D55E00",
        "Never → MIC (MICs entry)": "#009E73",
        "Never Gavi (always)": "#7F7F7F",
    }

    trajectories = [t for t in trajectory_order if t in df["gavi_trajectory"].unique()]
    if not trajectories:
        print("Available gavi_trajectory values:")
        print(df["gavi_trajectory"].dropna().unique())
        raise ValueError("No recognized gavi_trajectory categories found in NON-HIC data.")

    # ------------------------------------------------------------
    # Fit mixed-effects growth model
    # ------------------------------------------------------------
    ref = "Never Gavi (always)"
    if ref not in df["gavi_trajectory"].unique():
        ref = df["gavi_trajectory"].value_counts().idxmax()

    formula = f'vax_fd_cov ~ time * C(gavi_trajectory, Treatment(reference="{ref}"))'

    res = None
    try:
        mB = smf.mixedlm(formula=formula, data=df, groups=df["country_code"], re_formula="1 + time")
        res = mB.fit(method="lbfgs", reml=False)
        print("Model B fitted (random intercept + slope).")
    except Exception as e:
        print("Model B failed, falling back to Model A. Error:", repr(e))

    if res is None:
        mA = smf.mixedlm(formula=formula, data=df, groups=df["country_code"], re_formula="1")
        res = mA.fit(method="lbfgs", reml=False)
        print("Model A fitted (random intercept only).")

    print("Reference group:", ref, "| Converged:", getattr(res, "converged", "NA"))
    
    # If random-slope model did not converge, refit with random intercept only
    if hasattr(res, "converged") and (res.converged is False):
        print("WARNING: random-slope model did not converge. Refitting random-intercept model (Model A).")
        mA = smf.mixedlm(
            formula=formula,
            data=df,
            groups=df["country_code"],
            re_formula="1",
        )
        res = mA.fit(method="lbfgs", reml=False)
        print("Model A fitted (random intercept only). Converged:", getattr(res, "converged", "NA"))


    # ------------------------------------------------------------
    # Model output (console + txt)
    # ------------------------------------------------------------
    out_txt = outdir / "Model_Figure3_growth_model_NONHIC.txt"

    with open(out_txt, "w") as f:
        f.write(f"Formula: {formula}\n")
        f.write(f"Reference group: {ref}\n")
        f.write(f"Converged: {getattr(res, 'converged', 'NA')}\n\n")
        f.write(res.summary().as_text())
        f.write("\n")

    print("\n=== Growth model summary (fixed effects) ===")
    print(res.summary())
    print(f"\nSaved model summary: {out_txt}")


    # ------------------------------------------------------------
    # Extract fixed effects (best for reporting)
    # ------------------------------------------------------------
    fe = pd.DataFrame({
        "term": res.fe_params.index,
        "estimate": res.fe_params.values,
        "std_error": res.bse_fe.values if hasattr(res, "bse_fe") else np.nan,
    })

    # z-stats and p-values (approx normal, standard in statsmodels MixedLM)
    if hasattr(res, "bse_fe"):
        fe["z"] = fe["estimate"] / fe["std_error"]
        fe["p_value"] = 2 * (1 - norm.cdf(np.abs(fe["z"])))

    out_fe = outdir / "Table_Figure3_fixed_effects_growth_model_NONHIC.xlsx"
    fe.to_excel(out_fe, index=False, engine="openpyxl")
    print(f"Saved fixed effects table: {out_fe}")


    # ------------------------------------------------------------
    # Raw means table
    # ------------------------------------------------------------
    raw_means = (
        df.groupby(["year", "gavi_trajectory"], as_index=False)
        .agg(raw_mean=("vax_fd_cov", "mean"))
    )
    raw_means.to_excel(out_raw, index=False, engine="openpyxl")
    print(f"Saved raw means table: {out_raw}")

    # ------------------------------------------------------------
    # Predicted means grid (2015–2024)
    # ------------------------------------------------------------
    pred_grid = [{"gavi_trajectory": g, "time": t, "year": 2015 + t} for g in trajectories for t in range(0, 10)]
    pred_df = pd.DataFrame(pred_grid)
    pred_df["pred_mean"] = res.predict(pred_df)

    pred_df.to_excel(out_pred, index=False, engine="openpyxl")
    print(f"Saved predicted means table: {out_pred}")

    # ------------------------------------------------------------
    # Make two separate figures
    # ------------------------------------------------------------
    years_a = [2015, 2016, 2017, 2018, 2019]
    years_b = [2020, 2021, 2022, 2023, 2024]

    make_plot(
        outpath_pdf=out_pdf_a,
        outpath_png=(out_png_a if args.png else None),
        years=years_a,
        raw_means=raw_means,
        pred_df=pred_df,
        trajectories=trajectories,
        trajectory_label_map=trajectory_label_map,
        colors=COLORS,
        show_covid=False,
        show_2022=False,
        legend=True,
    )

    make_plot(
        outpath_pdf=out_pdf_b,
        outpath_png=(out_png_b if args.png else None),
        years=years_b,
        raw_means=raw_means,
        pred_df=pred_df,
        trajectories=trajectories,
        trajectory_label_map=trajectory_label_map,
        colors=COLORS,
        show_covid=True,
        show_2022=True,   # ONLY here
        legend=True,
    )

    fe_rounded = fe.copy()
    fe_rounded["estimate"] = fe_rounded["estimate"].round(2)
    fe_rounded["std_error"] = fe_rounded["std_error"].round(2)
    fe_rounded["z"] = fe_rounded["z"].round(2)
    fe_rounded["p_value"] = fe_rounded["p_value"].apply(
        lambda x: "<0.001" if x < 0.001 else f"{x:.3f}"
    )

    out_tex = outdir / "Table_Figure3_growth_model_NONHIC.tex"

    with open(out_tex, "w") as f:
        f.write(
            fe_rounded.to_latex(
                index=False,
                escape=False,
                column_format="lrrrr",
                caption="Growth model estimates of HPV first-dose coverage by Gavi status (non-HIC countries)",
                label="tab:gavi_growth_model",
            )
        )

    print(f"LaTeX table saved to: {out_tex}")

    print("DONE.")


if __name__ == "__main__":
    main()
