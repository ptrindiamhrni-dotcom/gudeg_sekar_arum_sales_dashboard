import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


st.set_page_config(
    page_title="Gudeg Sekar Arum | Mitra Online",
    layout="wide"
)

st.title("Gudeg Sekar Arum | Kinerja Penjualan 2025")
st.caption(
    "Data simulasi • 1 baris = outlet × tanggal × kanal. "
    "Diskon bukan bukti dampak kausal promo."
)

p = Path(__file__).resolve().parent / "Data_Transformasi_Gudeg_2025.csv"

if not p.is_file():
    st.error(f"File data tidak ditemukan: {p.name}")
    st.info("Letakkan file CSV di folder yang sama dengan dashboard.")
    st.stop()

try:
    df = pd.read_csv(p)
except (OSError, pd.errors.ParserError, UnicodeDecodeError) as e:
    st.error(f"File CSV gagal dibaca: {e}")
    st.stop()

df.columns = df.columns.astype(str).str.strip()

required = [
    "Tanggal",
    "Outlet",
    "Kanal_Penjualan",
    "Bulan",
    "Jenis_Hari",
    "Omzet_Bersih_Rp",
    "Omzet_Kotor_Rp",
    "Diskon_Rp",
    "Jumlah_Transaksi",
    "Jumlah_Ulasan",
    "Rating_Rata_rata",
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
    st.write("Kolom yang tersedia:", df.columns.tolist())
    st.stop()

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

numeric_cols = [
    "Omzet_Bersih_Rp",
    "Omzet_Kotor_Rp",
    "Diskon_Rp",
    "Jumlah_Transaksi",
    "Jumlah_Ulasan",
    "Rating_Rata_rata",
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")


invalid_dates = int(df["Tanggal"].isna().sum())
df = df.dropna(subset=["Tanggal"]).copy()

if df.empty:
    st.error("Tidak ada data dengan tanggal yang valid.")
    st.stop()

for col in [
    "Omzet_Bersih_Rp",
    "Omzet_Kotor_Rp",
    "Diskon_Rp",
    "Jumlah_Transaksi",
    "Jumlah_Ulasan",
]:
    df[col] = df[col].fillna(0)

df["Bulan"] = df["Bulan"].fillna(
    df["Tanggal"].dt.strftime("%Y-%m")
).astype(str)

for col in ["Outlet", "Kanal_Penjualan", "Jenis_Hari"]:
    df[col] = df[col].fillna("Tidak diketahui").astype(str).str.strip()
    df[col] = df[col].replace("", "Tidak diketahui")


a, b, c = st.columns(3)

outlet_options = sorted(df["Outlet"].unique().tolist())
kanal_options = sorted(df["Kanal_Penjualan"].unique().tolist())
bulan_options = sorted(df["Bulan"].unique().tolist())
jenis_options = sorted(df["Jenis_Hari"].unique().tolist())

out = a.multiselect(
    "Outlet",
    outlet_options,
    default=outlet_options
)

kan = b.multiselect(
    "Kanal",
    kanal_options,
    default=kanal_options
)

bulan = c.multiselect(
    "Bulan",
    bulan_options,
    default=bulan_options
)

jenis = st.multiselect(
    "Jenis hari",
    jenis_options,
    default=jenis_options
)

d = df[
    df["Outlet"].isin(out)
    & df["Kanal_Penjualan"].isin(kan)
    & df["Bulan"].isin(bulan)
    & df["Jenis_Hari"].isin(jenis)
].copy()

if invalid_dates:
    st.warning(
        f"{invalid_dates} baris dengan tanggal tidak valid "
        "dikeluarkan dari analisis."
    )

if d.empty:
    st.warning("Tidak ada data yang sesuai dengan filter pilihan.")
    st.stop()

net = d["Omzet_Bersih_Rp"].sum()
tr = d["Jumlah_Transaksi"].sum()
n = d["Jumlah_Ulasan"].sum()

valid_rating = (
    d["Rating_Rata_rata"].notna()
    & d["Jumlah_Ulasan"].gt(0)
)

rating_count = d.loc[valid_rating, "Jumlah_Ulasan"].sum()

rat = (
    (
        d.loc[valid_rating, "Rating_Rata_rata"]
        * d.loc[valid_rating, "Jumlah_Ulasan"]
    ).sum() / rating_count
    if rating_count > 0
    else float("nan")
)

kpi = st.columns(4)

kpi[0].metric("Omzet bersih", f"Rp{net:,.0f}")
kpi[1].metric("Transaksi", f"{tr:,.0f}")
kpi[2].metric(
    "Rata-rata per transaksi",
    f"Rp{net / tr:,.0f}" if tr > 0 else "—"
)
kpi[3].metric(
    "Rating berbobot",
    f"{rat:.2f} / 5" if pd.notna(rat) else "—"
)


left, right = st.columns(2)

with left:
    x = (
        d.groupby(pd.Grouper(key="Tanggal", freq="MS"))[
            "Omzet_Bersih_Rp"
        ]
        .sum()
        .reset_index()
    )

    x = x.dropna(subset=["Tanggal"])

    fig = px.line(
        x,
        x="Tanggal",
        y="Omzet_Bersih_Rp",
        markers=True,
        title="Tren omzet bersih bulanan",
        labels={
            "Tanggal": "Bulan",
            "Omzet_Bersih_Rp": "Omzet bersih (Rp)"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

with right:
    x = (
        d.groupby(["Outlet", "Kanal_Penjualan"], as_index=False)
        ["Omzet_Bersih_Rp"]
        .sum()
    )

    fig = px.bar(
        x,
        x="Outlet",
        y="Omzet_Bersih_Rp",
        color="Kanal_Penjualan",
        barmode="group",
        title="Outlet × kanal",
        labels={
            "Outlet": "Outlet",
            "Kanal_Penjualan": "Kanal penjualan",
            "Omzet_Bersih_Rp": "Omzet bersih (Rp)"
        }
    )

    st.plotly_chart(fig, use_container_width=True)


left, right = st.columns(2)

with left:
    x = (
        d.groupby("Kanal_Penjualan", as_index=False)
        ["Omzet_Bersih_Rp"]
        .sum()
    )

    if x["Omzet_Bersih_Rp"].sum() > 0:
        fig = px.pie(
            x,
            names="Kanal_Penjualan",
            values="Omzet_Bersih_Rp",
            title="Pangsa omzet kanal"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada omzet positif untuk ditampilkan.")


with right:
    online = d[
        d["Kanal_Penjualan"].str.strip().str.casefold()
        == "pesan antar online"
    ].copy()

    if not online.empty:
        online["Promo"] = online["Diskon_Rp"].gt(0).map({
            True: "Promo",
            False: "Nonpromo"
        })

        fig = px.box(
            online,
            x="Outlet",
            y="Omzet_Bersih_Rp",
            color="Promo",
            title="Distribusi omzet harian kanal online",
            labels={
                "Outlet": "Outlet",
                "Omzet_Bersih_Rp": "Omzet bersih (Rp)",
                "Promo": "Status promo"
            }
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "Tidak ada data kanal pesan antar online "
            "pada filter yang dipilih."
        )


st.subheader("Evaluasi diskon — deskriptif, bukan ROI")

if not online.empty:
    total_diskon = online["Diskon_Rp"].sum()
    omzet_kotor = online["Omzet_Kotor_Rp"].sum()

    rasio_diskon = (
        100 * total_diskon / omzet_kotor
        if omzet_kotor > 0
        else None
    )

    rasio_text = (
        f"{rasio_diskon:.2f}%"
        if rasio_diskon is not None
        else "Tidak dapat dihitung (omzet kotor nol)"
    )

    st.write(
        f"Diskon online pada filter: **Rp{total_diskon:,.0f}**; "
        f"omzet kotor online: **Rp{omzet_kotor:,.0f}**; "
        f"rasio diskon: **{rasio_text}**"
    )
else:
    st.info("Tidak ada data online pada filter yang dipilih.")

st.warning(
    "Perbedaan promo–nonpromo dapat dipengaruhi outlet, waktu, "
    "dan permintaan. Data ini tidak memiliki biaya, komisi platform, "
    "atau kelompok kontrol sehingga ROI maupun uplift tidak dapat "
    "disimpulkan."
)


with st.expander("Lihat data sesuai filter"):
    st.dataframe(d, use_container_width=True)

st.caption(
    "Sumber: Data Simulasi Penjualan Gudeg Sekar Arum 2025"
    
)