#!/usr/bin/env python3
# ============================================================
# gavi_analysis_2_own.py
#
# Figure 2: Mean gap to HIC mean HPV first-dose coverage by Gavi trajectory
# (NON-HIC only for plotted groups; HIC used only to form yearly benchmark).
#
# Styling: tueplots (ICML 2024, half column)
# Output: PDF (vector, always) + optional PNG preview + Excel table
#
# Updates vs your original:
#   - Robust style helper + optional --no_tex (recommended on macOS)
#   - Colorblind-safe, consistent palette across trajectories
#   - ONE legend inside the plot (no bbox_to_anchor outside)
#   - Optional 2020–2021 COVID shading (same reddish tone as Fig 1)
#   - Cleaner reference lines (0 pp + 2022 dashed) and lighter grid
# ============================================================

from pathlib import Path
import argparse

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from tueplots import bundles, figsizes


def configure_style(use_tex: bool = True):
    plt.rcParams.update(bundles.icml2025())
    plt.rcParams.update(figsizes.icml2025_half())

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
                # TeX-safe serif fallbacks (Times New Roman often brittle on macOS)
                "font.serif": ["Times", "TeX Gyre Termes", "Nimbus Roman", "DejaVu Serif"],
            }
        )
    else:
        plt.rcParams.update({"text.usetex": False})


def main():
    parser = argparse.ArgumentParser(description="Generate Figure 2 (gap to HIC mean by Gavi trajectory).")
    parser.add_argument("--input", type=str, required=True, help="Path to cleaned panel dataset (xlsx)")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory for figures and tables")
    parser.add_argument("--png", action="store_true", help="Also save a PNG preview (PDF is always saved).")

    # New switches (match Fig 1 workflow)
    parser.add_argument("--no_tex", action="store_true", help="Disable LaTeX text rendering (more robust).")
    parser.add_argument("--shade_covid", action="store_true", help="Shade 2020–2021 period.")
    parser.add_argument("--label_covid", action="store_true", help="Add 'COVID-19' label to shaded region.")
    args = parser.parse_args()

    configure_style(use_tex=not args.no_tex)

    input_xlsx = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_pdf = outdir / "Figure2_gap_to_HIC_mean_by_gavi_trajectory_NONHIC_2015_2024.pdf"
    out_png = outdir / "Figure2_gap_to_HIC_mean_by_gavi_trajectory_NONHIC_2015_2024.png"
    out_tbl = outdir / "Table_Figure2_gap_to_HIC_by_year_and_trajectory_NONHIC_2015_2024.xlsx"

    # ---------------------------
    # Load + validate data
    # ---------------------------
    df = pd.read_excel(input_xlsx, engine="openpyxl")

    required_cols = {"country_code", "year", "income_class", "vax_fd_cov", "gavi_trajectory"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)

    df["income_class"] = df["income_class"].astype("string").str.strip().str.upper()
    df["vax_fd_cov"] = pd.to_numeric(df["vax_fd_cov"], errors="coerce")
    df["gavi_trajectory"] = df["gavi_trajectory"].astype("string").str.strip()

    # Restrict window and valid rows
    df = df[df["year"].between(2015, 2024)].copy()
    df = df.dropna(subset=["country_code", "vax_fd_cov", "income_class"]).copy()

    # ---------------------------
    # 1) HIC benchmark: mean coverage by year (HIC only)
    # ---------------------------
    hic_mean_by_year = (
        df.loc[df["income_class"] == "H"]
        .groupby("year")["vax_fd_cov"]
        .mean()
        .rename("hic_mean_vax_fd_cov")
        .reset_index()
    )
    if hic_mean_by_year.empty:
        raise ValueError("No HIC observations found (income_class == 'H'). Cannot compute benchmark.")

    df = df.merge(hic_mean_by_year, on="year", how="left")

    # ---------------------------
    # 2) Gap to HIC mean (pp)
    # ---------------------------
    df["gap_to_hic_mean"] = df["hic_mean_vax_fd_cov"] - df["vax_fd_cov"]

    # ---------------------------
    # 3) NON-HIC only for plotted lines, require trajectory label
    # ---------------------------
    df_nonhic = df[(df["income_class"] != "H") & (df["gavi_trajectory"].notna())].copy()
    df_nonhic = df_nonhic.dropna(subset=["gap_to_hic_mean"]).copy()

    # ---------------------------
    # 4) Aggregate: mean gap by year & trajectory (NON-HIC only)
    # ---------------------------
    gap_summary = (
        df_nonhic.groupby(["year", "gavi_trajectory"], as_index=False)
        .agg(
            mean_gap=("gap_to_hic_mean", "mean"),
            n_countries=("country_code", "nunique"),
            n_obs=("gap_to_hic_mean", "size"),
        )
        .sort_values(["gavi_trajectory", "year"])
        .reset_index(drop=True)
    )

    gap_summary.to_excel(out_tbl, index=False, engine="openpyxl")
    print(f"Saved table: {out_tbl}")

    # ---------------------------
    # 5) Plot
    # ---------------------------
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

    # Colorblind-safe palette (keep "Never" gray)
    COLORS = {
        "Classic Gavi (always)": "#0072B2",        # blue
        "Classic → MIC (graduated)": "#D55E00",    # vermillion
        "Never → MIC (MICs entry)": "#009E73",     # green
        "Never Gavi (always)": "#7F7F7F",          # gray
    }

    present = [t for t in trajectory_order if t in gap_summary["gavi_trajectory"].unique().tolist()]
    if not present:
        print("Available gavi_trajectory values:")
        print(gap_summary["gavi_trajectory"].dropna().unique())
        raise ValueError("No recognized gavi_trajectory categories found in NON-HIC data.")

    fig, ax = plt.subplots(constrained_layout=True)

    # Optional COVID shading (match Fig 1 — reddish)
    if args.shade_covid:
        ax.axvspan(2020, 2021, color="#D55E00", alpha=0.10, zorder=0)
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

    # Lines
    for traj in present:
        sub = gap_summary[gap_summary["gavi_trajectory"] == traj].sort_values("year")
        pretty_label = trajectory_label_map.get(traj, traj)
        ax.plot(
            sub["year"],
            sub["mean_gap"],
            marker="o",
            markersize=4.2,
            markeredgewidth=0.8,
            linewidth=2.0,
            color=COLORS.get(traj, None),
            label=pretty_label,
        )

    # Reference lines
    ax.axhline(0, linewidth=1.0, alpha=0.8)
    ax.axvline(2022, linestyle="--", linewidth=1.0, alpha=0.9)

    ax.set_xlabel("Year")
    ax.set_ylabel("Gap to HIC mean (pp)")
    ax.set_title("")
    ax.set_xlim(2015, 2024)
    ax.set_xticks(list(range(2015, 2025, 1)))

    ymin = float(np.nanmin(gap_summary["mean_gap"]))
    ymax = float(np.nanmax(gap_summary["mean_gap"]))
    pad = 0.06 * (ymax - ymin) if ymax > ymin else 5.0
    ax.set_ylim(ymin - pad, ymax + pad)

    ax.grid(True, axis="y")
    ax.grid(False, axis="x")

    # ONE legend inside the plot
    leg = ax.legend(
        title="Gavi Status",
        loc="lower left",
        fontsize=3,
        title_fontsize=4,
        handlelength=0.8,
        handletextpad=0.7,
        borderpad=0.4,
        labelspacing=0.4,
    )

    # Save
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.02, transparent=True)
    print(f"Saved PDF figure: {out_pdf}")

    if args.png:
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02, transparent=True)
        print(f"Saved PNG preview: {out_png}")

    plt.close(fig)

    # ---------------------------
    # 6) Quick prints (debug)
    # ---------------------------
    print("\n=== HIC benchmark (mean coverage) by year ===")
    print(hic_mean_by_year.to_string(index=False))

    print("\n=== Mean gap in 2015 vs 2024 by trajectory (NON-HIC only) ===")
    wide = gap_summary.pivot(index="gavi_trajectory", columns="year", values="mean_gap")
    cols = [c for c in [2015, 2024] if c in wide.columns]
    if cols:
        print(wide[cols].sort_index().to_string())
    else:
        print("2015/2024 columns not found in pivot (check year coverage).")


if __name__ == "__main__":
    main()
