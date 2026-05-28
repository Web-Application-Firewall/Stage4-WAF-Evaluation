import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec

from matplotlib.ticker import MultipleLocator
from datetime import datetime, timedelta
from pathlib import Path

# ════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════

ARCHIVO = "../collection/coraza_statistics_esc_1.txt"
OUTPUT_IMAGE = "../results/monitoreo_bajo.png"

VENTANA_SUAVIZADO = 30
SALTAR_MUESTRAS = 1
RAM_TOTAL_GIB = 15.1  

# ════════════════════════════════════════
# PALETA (FONDO BLANCO)
# ════════════════════════════════════════

P = {
    "bg":       "#ffffff",
    "panel":    "#f5f7fc",
    "grid":     "#dde2ef",
    "cpu":      "#0077cc",
    "mem":      "#e03030",
    "smooth":   "#111111",
    "text":     "#1a1d2e",
    "subtext":  "#6b7080",
    "accent":   "#c47a00",
}

# ════════════════════════════════════════
# CONTROL DE FECHAS
# ════════════════════════════════════════

base_date = datetime(2026, 5, 10)

current_day = 0
previous_time = None

# ════════════════════════════════════════
# PARSEO
# ════════════════════════════════════════

timestamps = []
cpu_values = []
mem_values = []

current_mem = None

with open(ARCHIVO, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:

    # ─────────────────────────────────────
    # MEMORIA
    # ─────────────────────────────────────

    mem_match = re.search(
        r'(\d+:\d+:\d+\s+[AP]M).*?(\d+\.\d+)\s+coraza$',
        line
    )

    if mem_match and "%MEM" not in line:
        current_mem = float(mem_match.group(2))

    # ─────────────────────────────────────
    # CPU
    # ─────────────────────────────────────

    cpu_match = re.search(
        r'(\d+:\d+:\d+\s+[AP]M)\s+'
        r'\d+\s+'          # UID
        r'\d+\s+'          # PID
        r'[\d.]+\s+'       # %usr
        r'[\d.]+\s+'       # %system
        r'[\d.]+\s+'       # %guest
        r'[\d.]+\s+'       # %wait
        r'([\d.]+)\s+'     # %CPU
        r'\d+\s+'          # CPU core
        r'coraza$',
        line
    )

    if cpu_match and "%CPU" not in line:

        time_obj = datetime.strptime(
            cpu_match.group(1),
            "%I:%M:%S %p"
        )

        if previous_time and time_obj.time() < previous_time:
            current_day += 1

        previous_time = time_obj.time()

        ts = datetime.combine(
            base_date.date() + timedelta(days=current_day),
            time_obj.time()
        )

        timestamps.append(ts)
        cpu_values.append(float(cpu_match.group(2)))
        mem_values.append(current_mem)


# ════════════════════════════════════════
# DATAFRAME
# ════════════════════════════════════════

df = pd.DataFrame({
    "timestamp": timestamps,
    "CPU": cpu_values,
    "MEM": mem_values
})

print(f"\n📊 MONITOREO DE CORAZA")
print(f"─" * 50)
print(f"  Muestras brutas cargadas:    {len(df):,}")

df = df.iloc[::SALTAR_MUESTRAS].reset_index(drop=True)

print(f"  Muestras procesadas (1 de cada {SALTAR_MUESTRAS}):  {len(df):,}")
print(
    f"  Rango de tiempo: "
    f"10 de mayo {df['timestamp'].iloc[0].strftime('%H:%M:%S')} "
    f"→ "
    f"11 de mayo {df['timestamp'].iloc[-1].strftime('%H:%M:%S')}"
)

# ════════════════════════════════════════
# CONVERTIR MEMORIA A GIB
# ════════════════════════════════════════

df["MEM_GIB"] = (df["MEM"] / 100) * RAM_TOTAL_GIB

# ════════════════════════════════════════
# SUAVIZADO
# ════════════════════════════════════════

df["CPU_smooth"] = (
    df["CPU"]
    .rolling(window=VENTANA_SUAVIZADO, center=True, min_periods=1)
    .mean()
)

df["MEM_GIB_smooth"] = (
    df["MEM_GIB"]
    .rolling(window=VENTANA_SUAVIZADO, center=True, min_periods=1)
    .mean()
)

# ════════════════════════════════════════
# FIGURA CON GRIDSPEC
# ════════════════════════════════════════

fig = plt.figure(figsize=(16, 9), facecolor=P["bg"])

duration = df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]
h, rem = divmod(int(duration.total_seconds()), 3600)
mins = rem // 60

fig.suptitle(
    "Monitoreo de Coraza escenario bajo",
    fontsize=18,
    fontweight="bold",
    color=P["text"],
    y=0.97
)

meta = (
    f"Duración: {h}h {mins}m  |  "
    f"Muestras: {len(df):,}m | "
    f"RAM total: {15.1} GiB"
)
fig.text(0.5, 0.935, meta, ha="center", fontsize=9, color=P["subtext"])

gs = gridspec.GridSpec(2, 1, figure=fig,
                       hspace=0.45, top=0.91, bottom=0.09,
                       left=0.07, right=0.97)
ax_cpu = fig.add_subplot(gs[0])
ax_mem = fig.add_subplot(gs[1])

# ════════════════════════════════════════
# FUNCION DIBUJO
# ════════════════════════════════════════

def draw(ax, ts, raw, label, unit, color, ymax, ref_val=None, ref_label=None):

    ax.set_facecolor(P["panel"])

    for sp in ax.spines.values():
        sp.set_color(P["grid"])

    rolled = (
        raw
        .rolling(window=VENTANA_SUAVIZADO, center=True, min_periods=1)
        .mean()
    )

    ax.fill_between(ts, raw, alpha=0.18, color=color)
    ax.plot(ts, raw, color=color, linewidth=0.6, alpha=0.55)
    ax.plot(
        ts, rolled,
        color=P["smooth"],
        linewidth=1.5,
        label=f"Media móvil ({VENTANA_SUAVIZADO} muestras)"
    )

    if ref_val is not None:
        ax.axhline(
            ref_val,
            color=P["accent"],
            linewidth=0.9,
            linestyle=":",
            alpha=0.9,
            label=ref_label
        )

    stats = {
        "min": raw.min(),
        "max": raw.max(),
        "mean": raw.mean(),
        "p95": raw.quantile(0.95)
    }

    ax.set_title(
        f"  Mín: {stats['min']:.2f}{unit}   Máx: {stats['max']:.2f}{unit}   "
        f"Prom: {stats['mean']:.2f}{unit}   P95: {stats['p95']:.2f}{unit}  ",
        fontsize=8.5,
        color=P["accent"],
        loc="right",
        pad=6
    )

    ax.set_xlim(ts.iloc[0], ts.iloc[-1])
    ax.set_ylim(0, ymax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=12))
    ax.tick_params(colors=P["subtext"], labelsize=8)
    ax.set_ylabel(f"{label} ({unit})", color=P["text"], fontsize=10)
    ax.set_xlabel("Hora", color=P["subtext"], fontsize=8)
    ax.yaxis.set_major_locator(MultipleLocator(max(ymax / 5, 1)))
    ax.grid(True, color=P["grid"], linewidth=0.5, linestyle="--")
    ax.legend(
        fontsize=8,
        loc="upper left",
        facecolor=P["bg"],
        edgecolor=P["grid"],
        labelcolor=P["subtext"]
    )

# ════════════════════════════════════════
# CPU
# ════════════════════════════════════════

cpu_ymax = 50
draw(
    ax_cpu, df["timestamp"], df["CPU"],
    "CPU", "%", P["cpu"], cpu_ymax,
    ref_val=100, ref_label="100 %"
)

# ════════════════════════════════════════
# MEMORIA (EN GIB)
# ════════════════════════════════════════

# Si MEM_GIB existe:
df["MEM_MB"] = df["MEM_GIB"] * 1024

mem_mb_ymax = 50

draw(
    ax_mem,
    df["timestamp"],
    df["MEM_MB"],
    "Memoria usada",
    "MB",
    P["mem"],
    mem_mb_ymax
)
# ════════════════════════════════════════
# PIE DE PÁGINA
# ════════════════════════════════════════

fig.text(
    0.5, 0.01,
    "monitoreocoraza.py",
    ha="center",
    fontsize=7.5,
    color=P["subtext"]
)

# ════════════════════════════════════════
# GUARDAR — DPI AUMENTADO A 300
# ════════════════════════════════════════

plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=1600, bbox_inches="tight", facecolor=P["bg"])
print(f"\n✅ Imagen guardada: {OUTPUT_IMAGE}")
print(f"─" * 50 + "\n")