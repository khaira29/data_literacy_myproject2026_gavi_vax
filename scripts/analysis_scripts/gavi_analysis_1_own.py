#!/usr/bin/env python3
# ============================================================
# gavi_analysis_1.py
#
# Figure 1: Mean HPV first-dose coverage over time (HIC vs non-HIC)
# Styling: tueplots (ICML 2024, half column) + LaTeX text rendering
#
# Improvements vs your current version:
#   - Robust TeX/Times fallback (won't crash on macOS)
#   - Colorblind-safe palette + lighter markers
#   - Optional 95% CI ribbon (country-level bootstrap by year-group)
#   - Cleaner COVID shading with label (optional)
#   - Better grid/spines + legend styling for 2-column paper
#
# Outputs:
#   - PDF (vector) (always)
#   - PNG preview (optional)
#   - Excel summary table (means + N) + optional CI table
# ============================================================

from pathlib import Path
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from tueplots import bundles, figsizes


# ---------------------------
# Style helpers
# ---------------------------
def configure_style(use_tex: bool = True):
    """ICML 2024 half-column styling with robust fallbacks."""
    plt.rcParams.update(bundles.icml2024())
    plt.rcParams.update(figsizes.icml2024_half())

    # Slightly nicer defaults for publication
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
        # TeX can be brittle; keep it optional and fallback gracefully
        plt.rcParams.update(
            {
                "text.usetex": True,
                "font.family": "serif",
                # Times New Roman often unavailable in TeX on macOS; use TeX-safe serif.
                # If your TeX install has Times, it will still look Times-like.
                "font.serif": ["Times", "Times New Roman", "TeX Gyre Termes", "Nimbus Roman", "DejaVu Serif"],
            }
        )
    else:
        plt.rcParams.update({"text.usetex": False})


def bootstrap_ci_country_mean(
    df: pd.DataFrame,
    group_cols=("year", "income_group"),
    value_col="vax_fd_cov",
    country_col="country_code",
    n_boot: int = 800,
    seed: int = 7,
):
    """
    Bootstrap 95% CI of the mean by resampling countries WITHIN each group.
    This respects clustering (country-year panel).
    Returns a dataframe with mean, ci_low, ci_high, and counts.
    """
    rng = np.random.default_rng(seed)

    out_rows = []
    grouped = df.groupby(list(group_cols))

    for keys, g in grouped:
        # Country-level means within this group (year x income_group)
        by_country = g.groupby(country_col, as_index=False)[value_col].mean()
        vals = by_country[value_col].dropna().to_numpy()

        if len(vals) == 0:
            continue

        mean = float(np.mean(vals))
        n_countries = int(by_country[country_col].nunique())
        n_obs = int(g.shape[0])

        # If only one country, CI is degenerate
        if len(vals) == 1:
            ci_low = ci_high = mean
        else:
            boot_means = np.empty(n_boot, dtype=float)
            for b in range(n_boot):
                sample = rng.choice(vals, size=len(vals), replace=True)
                boot_means[b] = np.mean(sample)
            ci_low, ci_high = np.quantile(boot_means, [0.025, 0.975]).tolist()

        if isinstance(keys, tuple):
            row = dict(zip(group_cols, keys))
        else:
            row = {group_cols[0]: keys}

        row.update(
            {
                "mean_cov": mean,
                "ci_low": float(ci_low),
                "ci_high": float(ci_high),
                "n_countries": n_countries,
                "n_obs": n_obs,
            }
        )
        out_rows.append(row)

    return pd.DataFrame(out_rows).sort_values(list(group_cols)).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Generate Figure 1 (HIC vs non-HIC mean coverage).")
    parser.add_argument("--input", type=str, required=True, help="Path to cleaned panel dataset (xlsx)")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory for figures and tables")
    parser.add_argument("--png", action="store_true", help="Also save a PNG preview (PDF is always saved).")

    # New switches
    parser.add_argument("--no_tex", action="store_true", help="Disable LaTeX text rendering (more robust).")
    parser.add_argument("--ci", action="store_true", help="Add 95% bootstrap CI ribbon (country-resampling).")
    parser.add_argument("--n_boot", type=int, default=800, help="Bootstrap draws for CI (default: 800).")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for CI bootstrap (default: 7).")

    # COVID shading options
    parser.add_argument("--shade_covid", action="store_true", help="Shade 2020–2021 period.")
    parser.add_argument("--label_covid", action="store_true", help="Add 'COVID-19' label to shaded region.")

    args = parser.parse_args()

    # Configure style early
    configure_style(use_tex=not args.no_tex)

    input_xlsx = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_pdf = outdir / "Figure1_mean_hpv_first_dose_HIC_vs_nonHIC_2015_2024.pdf"
    out_png = outdir / "Figure1_mean_hpv_first_dose_HIC_vs_nonHIC_2015_2024.png"
    out_tbl = outdir / "Table_Figure1_mean_hpv_first_dose_HIC_vs_nonHIC_2015_2024.xlsx"
    out_ci_tbl = outdir / "Table_Figure1_mean_hpv_first_dose_HIC_vs_nonHIC_2015_2024_with_CI.xlsx"

    # ---------------------------
    # Load + validate data
    # ---------------------------
    df = pd.read_excel(input_xlsx, engine="openpyxl")

    required_cols = {"country_code", "year", "income_class", "vax_fd_cov"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Clean types
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)

    df["income_class"] = df["income_class"].astype("string").str.strip().str.upper()
    df["vax_fd_cov"] = pd.to_numeric(df["vax_fd_cov"], errors="coerce")

    # Restrict window and non-missing coverage
    df = df[df["year"].between(2015, 2024)].copy()
    df = df.dropna(subset=["vax_fd_cov", "income_class", "country_code"]).copy()

    # Define groups
    df["income_group"] = np.where(df["income_class"] == "H", "HIC", "Non-HIC")

    # ---------------------------
    # Summaries (mean + counts)
    # ---------------------------
    mean_cov = (
        df.groupby(["year", "income_group"], as_index=False)
        .agg(
            mean_cov=("vax_fd_cov", "mean"),
            n_countries=("country_code", "nunique"),
            n_obs=("vax_fd_cov", "size"),
        )
        .sort_values(["income_group", "year"])
        .reset_index(drop=True)
    )

    mean_cov.to_excel(out_tbl, index=False, engine="openpyxl")
    print(f"Saved table: {out_tbl}")

    # Optional CI table (bootstrap at country level)
    ci_cov = None
    if args.ci:
        ci_cov = bootstrap_ci_country_mean(
            df,
            group_cols=("year", "income_group"),
            value_col="vax_fd_cov",
            country_col="country_code",
            n_boot=args.n_boot,
            seed=args.seed,
        )
        ci_cov.to_excel(out_ci_tbl, index=False, engine="openpyxl")
        print(f"Saved CI table: {out_ci_tbl}")

    # ---------------------------
    # Plot
    # ---------------------------
    # Okabe–Ito inspired colors (colorblind-safe)
    COLORS = {"HIC": "#0072B2", "Non-HIC": "#E69F00"}

    fig, ax = plt.subplots(constrained_layout=True)

    # Optional COVID shading (very light)
    if args.shade_covid:
        ax.axvspan(
        2020, 2021,
        color="#D55E00",   # Okabe–Ito vermillion (red-orange)
        alpha=0.10,
        zorder=0,
    )

        if args.label_covid:
            ax.text(
                2020.5,
                0.98,
                "COVID-19",
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=8,
                color="#D55E00",
                alpha=0.9,
)


    # Draw series
    for grp in ["HIC", "Non-HIC"]:
        sub = mean_cov[mean_cov["income_group"] == grp].sort_values("year")

        ax.plot(
            sub["year"],
            sub["mean_cov"],
            label=grp,
            color=COLORS[grp],
            linewidth=2.0,
            marker="o",
            markersize=4.2,          # smaller markers for paper
            markeredgewidth=0.8,
        )

        # Optional CI ribbon
        if ci_cov is not None:
            cis = ci_cov[ci_cov["income_group"] == grp].sort_values("year")
            # Ensure aligned x
            ax.fill_between(
                cis["year"].to_numpy(),
                cis["ci_low"].to_numpy(),
                cis["ci_high"].to_numpy(),
                color=COLORS[grp],
                alpha=0.15,
                linewidth=0,
                zorder=1,
            )

        # Endpoint label (reduces need for legend emphasis)
        last = sub.iloc[-1]
        #ax.annotate(
            #f"{grp}",
           # xy=(last["year"], last["mean_cov"]),
           # xytext=(6, 0),
           # textcoords="offset points",
           # va="center",
            #fontsize=8,
            #color=COLORS[grp],
        #)

    # Axes and grid
    ax.set_xlabel("Year")
    ax.set_ylabel(r"HPV first-dose coverage (\%)")

    ax.set_xlim(2015, 2024)
    ax.set_xticks(list(range(2015, 2025, 1)))
    ax.grid(True, axis="y")
    ax.grid(False, axis="x")

    # Legend: keep, but make compact (endpoint labels already help)
    ax.legend(loc="upper left", handlelength=2.0)

    # Tight y-limits with a bit of padding (optional)
    ymin = float(mean_cov["mean_cov"].min())
    ymax = float(mean_cov["mean_cov"].max())
    pad = max(2.0, 0.06 * (ymax - ymin))
    ax.set_ylim(max(0, ymin - pad), min(100, ymax + pad))

    # ---------------------------
    # Save
    # ---------------------------
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.02, transparent=True)
    print(f"Saved PDF figure: {out_pdf}")

    if args.png:
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02, transparent=True)
        print(f"Saved PNG preview: {out_png}")

    plt.close(fig)


if __name__ == "__main__":
    main()
