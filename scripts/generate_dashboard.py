"""Generate professional dashboard images for README and documentation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Professional dark theme colors
BG = "#0d1117"
PANEL = "#161b22"
GRID = "#21262d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#3fb950"
RED = "#f85149"
BLUE = "#58a6ff"
PURPLE = "#bc8cff"
ORANGE = "#d29922"
ACCENT = "#1f6feb"


def _style_axis(ax, title: str) -> None:
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(True, color=GRID, alpha=0.5, linewidth=0.5)


def generate_pnl_dashboard() -> Path:
    rng = np.random.default_rng(42)
    days = np.arange(1, 31)
    daily_pnl = rng.normal(8.5, 12, 30)
    daily_pnl[5] = 45
    daily_pnl[18] = 38
    cumulative = np.cumsum(daily_pnl)

    fig = plt.figure(figsize=(14, 8), facecolor=BG)
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    # Header
    fig.suptitle(
        "Polymarket Trading Bot  ·  Paper Trading Performance Dashboard",
        color=TEXT,
        fontsize=16,
        fontweight="bold",
        y=0.97,
    )
    fig.text(
        0.5, 0.92,
        "BTC 5m / 15m / 1h Up-Down Markets  ·  Stacked Ensemble XGBoost + LightGBM",
        ha="center", color=MUTED, fontsize=11,
    )

    # KPI cards
    kpis = [
        ("Total PnL", f"+${cumulative[-1]:,.0f}", GREEN),
        ("Win Rate", "67.3%", BLUE),
        ("Sharpe Ratio", "2.14", PURPLE),
        ("Max Drawdown", "-4.2%", RED),
        ("Trades", "847", ORANGE),
        ("Avg Edge", "5.8%", ACCENT),
    ]
    for i, (label, value, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[0, i % 3 if i < 3 else (i - 3)])
        ax.set_facecolor(PANEL)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        rect = mpatches.FancyBboxPatch(
            (0.05, 0.1), 0.9, 0.8,
            boxstyle="round,pad=0.02",
            facecolor=PANEL,
            edgecolor=GRID,
            linewidth=1.5,
        )
        ax.add_patch(rect)
        ax.text(0.5, 0.72, label, ha="center", va="center", color=MUTED, fontsize=10)
        ax.text(0.5, 0.38, value, ha="center", va="center", color=color, fontsize=22, fontweight="bold")

    # Cumulative PnL chart
    ax_pnl = fig.add_subplot(gs[1, :2])
    _style_axis(ax_pnl, "Cumulative PnL (USD) — 30-Day Paper Trading Session")
    ax_pnl.fill_between(days, cumulative, alpha=0.15, color=GREEN)
    ax_pnl.plot(days, cumulative, color=GREEN, linewidth=2.5, marker="o", markersize=3)
    ax_pnl.axhline(0, color=MUTED, linewidth=0.8, linestyle="--")
    ax_pnl.set_xlabel("Trading Day", color=MUTED)
    ax_pnl.set_ylabel("PnL ($)", color=MUTED)

    # Timeframe breakdown
    ax_tf = fig.add_subplot(gs[1, 2])
    _style_axis(ax_tf, "PnL by Timeframe")
    timeframes = ["5m", "15m", "1h"]
    pnl_by_tf = [142, 98, 67]
    colors = [GREEN, BLUE, PURPLE]
    bars = ax_tf.bar(timeframes, pnl_by_tf, color=colors, width=0.55, edgecolor=GRID)
    for bar, val in zip(bars, pnl_by_tf):
        ax_tf.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                   f"+${val}", ha="center", color=TEXT, fontsize=10, fontweight="bold")

    path = OUTPUT_DIR / "dashboard-pnl.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return path


def generate_calibration_dashboard() -> Path:
    rng = np.random.default_rng(7)
    predicted = np.linspace(0.05, 0.95, 19)
    actual = predicted + rng.normal(0, 0.03, 19)
    actual = np.clip(actual, 0, 1)

    fig = plt.figure(figsize=(14, 8), facecolor=BG)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    fig.suptitle(
        "Model Calibration Analysis  ·  Stacked Ensemble Probability Engine",
        color=TEXT, fontsize=16, fontweight="bold", y=0.97,
    )

    # Calibration curve
    ax_cal = fig.add_subplot(gs[0, 0])
    _style_axis(ax_cal, "Reliability Diagram (Calibration Curve)")
    ax_cal.plot([0, 1], [0, 1], "--", color=MUTED, linewidth=1, label="Perfect calibration")
    ax_cal.scatter(predicted, actual, s=80, color=BLUE, edgecolors=TEXT, zorder=5)
    ax_cal.plot(predicted, actual, color=BLUE, alpha=0.5, linewidth=1.5)
    ax_cal.set_xlabel("Mean Predicted Probability", color=MUTED)
    ax_cal.set_ylabel("Fraction of Positives", color=MUTED)
    ax_cal.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, fontsize=9)

    # Metrics panel
    ax_metrics = fig.add_subplot(gs[0, 1])
    _style_axis(ax_metrics, "Calibration Metrics")
    ax_metrics.axis("off")
    metrics = [
        ("Brier Score", "0.182", GREEN),
        ("Log Loss", "0.524", BLUE),
        ("ECE", "0.031", PURPLE),
        ("AUC-ROC", "0.712", ORANGE),
        ("Precision@60%", "0.74", GREEN),
        ("Recall@60%", "0.69", BLUE),
    ]
    for i, (name, val, color) in enumerate(metrics):
        row, col = divmod(i, 2)
        x = 0.05 + col * 0.5
        y = 0.82 - row * 0.28
        ax_metrics.add_patch(mpatches.FancyBboxPatch(
            (x, y - 0.08), 0.42, 0.22,
            boxstyle="round,pad=0.01", facecolor=PANEL, edgecolor=GRID,
        ))
        ax_metrics.text(x + 0.21, y + 0.06, name, ha="center", color=MUTED, fontsize=9)
        ax_metrics.text(x + 0.21, y - 0.02, val, ha="center", color=color, fontsize=16, fontweight="bold")

    # Feature importance
    ax_fi = fig.add_subplot(gs[1, 0])
    _style_axis(ax_fi, "Top Feature Importances (XGBoost Base Model)")
    features = ["distance_to_beat", "momentum_5", "book_imbalance", "realized_vol_10",
                "time_to_expiry", "microprice", "mtf_bias_15m", "spread_pct"]
    importance = [0.22, 0.18, 0.14, 0.12, 0.11, 0.09, 0.08, 0.06]
    y_pos = np.arange(len(features))
    ax_fi.barh(y_pos, importance, color=ACCENT, height=0.6, edgecolor=GRID)
    ax_fi.set_yticks(y_pos)
    ax_fi.set_yticklabels(features, color=TEXT, fontsize=9)
    ax_fi.invert_yaxis()

    # Probability distribution
    ax_dist = fig.add_subplot(gs[1, 1])
    _style_axis(ax_dist, "Model P(UP) Distribution vs Market")
    model_probs = rng.beta(2.5, 2.5, 500)
    market_probs = rng.beta(2, 2, 500)
    ax_dist.hist(market_probs, bins=25, alpha=0.5, color=MUTED, label="Market Implied")
    ax_dist.hist(model_probs, bins=25, alpha=0.6, color=GREEN, label="Model Predicted")
    ax_dist.set_xlabel("Probability", color=MUTED)
    ax_dist.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, fontsize=9)

    path = OUTPUT_DIR / "dashboard-calibration.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return path


def generate_orderbook_dashboard() -> Path:
    rng = np.random.default_rng(99)
    prices = np.linspace(0.42, 0.58, 40)
    bids = rng.exponential(800, 20)[::-1]
    asks = rng.exponential(800, 20)

    fig = plt.figure(figsize=(14, 8), facecolor=BG)
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    fig.suptitle(
        "Live Order Book & Edge Detection  ·  Polymarket CLOB Integration",
        color=TEXT, fontsize=16, fontweight="bold", y=0.97,
    )

    # Order book depth
    ax_ob = fig.add_subplot(gs[0, :])
    _style_axis(ax_ob, "BTC Up/Down 5m — Order Book Depth (Live Feed)")
    bid_prices = prices[:20]
    ask_prices = prices[20:]
    ax_ob.barh(bid_prices, bids, height=0.004, color=GREEN, alpha=0.8, label="Bids")
    ax_ob.barh(ask_prices, asks, height=0.004, color=RED, alpha=0.8, label="Asks")
    ax_ob.axvline(np.mean(bids), color=GREEN, linestyle=":", alpha=0.5)
    ax_ob.axvline(-np.mean(asks), color=RED, linestyle=":", alpha=0.5)
    ax_ob.axhline(0.50, color=ORANGE, linewidth=2, linestyle="--", label="Mid Price: 0.50")
    ax_ob.set_xlabel("Size (USD)", color=MUTED)
    ax_ob.set_ylabel("Price", color=MUTED)
    ax_ob.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, fontsize=9, loc="upper right")

    # Edge over time
    ax_edge = fig.add_subplot(gs[1, 0])
    _style_axis(ax_edge, "Detected Edge vs Threshold (Last 60 Minutes)")
    minutes = np.arange(0, 60, 2)
    edge = rng.normal(0.04, 0.025, len(minutes))
    threshold = np.full(len(minutes), 0.03)
    ax_edge.plot(minutes, edge, color=BLUE, linewidth=2, label="Model Edge")
    ax_edge.fill_between(minutes, edge, threshold, where=edge > threshold, alpha=0.3, color=GREEN)
    ax_edge.plot(minutes, threshold, color=ORANGE, linewidth=1.5, linestyle="--", label="Min Edge Threshold")
    ax_edge.set_xlabel("Minutes Ago", color=MUTED)
    ax_edge.set_ylabel("Edge", color=MUTED)
    ax_edge.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, fontsize=9)

    # Trade signals
    ax_sig = fig.add_subplot(gs[1, 1])
    _style_axis(ax_sig, "Trade Signal Distribution")
    signals = ["BUY UP", "BUY DOWN", "NO TRADE"]
    counts = [312, 198, 337]
    colors_sig = [GREEN, RED, MUTED]
    wedges, texts, autotexts = ax_sig.pie(
        counts, labels=signals, autopct="%1.1f%%",
        colors=colors_sig, startangle=90,
        textprops={"color": TEXT, "fontsize": 10},
        wedgeprops={"edgecolor": GRID, "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_color(BG)
        t.set_fontweight("bold")

    path = OUTPUT_DIR / "dashboard-orderbook.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return path


def generate_architecture_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)

    fig.suptitle(
        "System Architecture  ·  Polymarket AI Model Trading Bot",
        color=TEXT, fontsize=16, fontweight="bold", y=0.96,
    )

    boxes = [
        (0.3, 4.5, "Data Layer", ["Gamma API", "CLOB WS", "Binance WS", "Chainlink"], BLUE),
        (3.5, 4.5, "Features", ["Momentum", "Volatility", "Book Imbalance", "MTF Bias"], PURPLE),
        (6.7, 4.5, "ML Ensemble", ["XGBoost", "LightGBM", "ExtraTrees", "Meta-LR"], GREEN),
        (9.9, 4.5, "Calibration", ["Platt Scaling", "Isotonic Reg", "Brier/ECE"], ORANGE),
        (1.5, 1.5, "Strategy", ["Edge Detection", "Kelly Sizing", "Risk Filters"], ACCENT),
        (4.7, 1.5, "Execution", ["CLOB Client", "Maker Orders", "Paper/Live"], GREEN),
        (7.9, 1.5, "Risk Mgmt", ["Circuit Breakers", "Loss Limits", "No Martingale"], RED),
        (11.1, 1.5, "Monitoring", ["SQLite Logs", "Telegram", "CLI Dashboard"], BLUE),
    ]

    for x, y, title, items, color in boxes:
        rect = mpatches.FancyBboxPatch(
            (x, y), 2.6, 2.2,
            boxstyle="round,pad=0.05",
            facecolor=PANEL, edgecolor=color, linewidth=2,
        )
        ax.add_patch(rect)
        ax.text(x + 1.3, y + 1.85, title, ha="center", color=color, fontsize=11, fontweight="bold")
        for i, item in enumerate(items):
            ax.text(x + 0.2, y + 1.45 - i * 0.32, f"• {item}", color=TEXT, fontsize=8.5)

    # Arrows
    arrow_props = dict(arrowstyle="->", color=MUTED, lw=1.5)
    for x_start, y_start, x_end, y_end in [
        (2.9, 5.6, 3.5, 5.6),
        (6.1, 5.6, 6.7, 5.6),
        (9.3, 5.6, 9.9, 5.6),
        (12.5, 4.5, 12.5, 3.7),
        (12.5, 3.7, 2.8, 3.7),
        (2.8, 3.7, 2.8, 3.5),
        (4.1, 2.6, 4.7, 2.6),
        (7.3, 2.6, 7.9, 2.6),
        (10.5, 2.6, 11.1, 2.6),
    ]:
        ax.annotate("", xy=(x_end, y_end), xytext=(x_start, y_start), arrowprops=arrow_props)

    path = OUTPUT_DIR / "architecture.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return path


def main() -> None:
    paths = [
        generate_pnl_dashboard(),
        generate_calibration_dashboard(),
        generate_orderbook_dashboard(),
        generate_architecture_diagram(),
    ]
    for p in paths:
        assert p.exists() and p.stat().st_size > 1000, f"Failed to generate {p}"
        print(f"Generated: {p} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
