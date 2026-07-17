import streamlit as st
import pandas as pd
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="🎬 VOD & IPTV Platformu", page_icon="🍿", layout="wide")

# İndirme Sepeti İçin Oturum Hafızası (Session State)
if "download_cart" not in st.session_state:
    st.session_state.download_cart = {}

st.markdown("""
    <style>
    .film-title { font-size: 16px; font-weight: bold; margin-top: 10px; height: 50px; overflow: hidden; text-overflow: ellipsis; }
    
    .action-btn {
        display: block;
        width: 100%;
        text-align: center;
        padding: 8px;
        border-radius: 5px;
        margin-top: 5px;
        text-decoration: none !important;
        font-weight: bold;
        color: white !important;
        font-size: 14px;
        transition: 0.3s;
    }
    .watch-btn { background-color: #E50914; border: 1px solid #E50914; }
    .watch-btn:hover { background-color: #b20710; border-color: #b20710; }
    .download-btn { background-color: #28a745; border: 1px solid #28a745; }
    .download-btn:hover { background-color: #218838; border-color: #218838; }
    </style>
""", unsafe_allow_html=True)

st.title("🍿 Film, Dizi ve Canlı TV Merkezi")
st.markdown("İçerikleri doğrudan izleyin, indirin veya toplu indirme için sepetinize ekleyin.")

@st.cache_data
def parse_m3u(file_content):
    lines = file_content.split('\n')
    data = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            logo_match = re.search(r'tvg-logo="(.*?)"', line)
            logo = logo_match.group(1).strip() if logo_match and logo_match.group(1) else ""
            if not logo.startswith("http"):
                logo = "https://via.placeholder.com/300x450.png?text=Kapak+Yok"
            
            cat_match = re.search(r'group-title="(.*?)"', line)
            category = cat_match.group(1).strip() if cat_match else "Diğer"
            
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else "İsimsiz İçerik"
            
            url = ""
            if i + 1 < len(lines) and not lines[i+1].startswith('#'):
                url = lines[i+1].strip()
                i += 1
            
            data.append({"İsim": name, "Kategori": category, "Logo": logo, "URL": url})
        i += 1
    return pd.DataFrame(data)

# --- SEPET VE TOPLU İNDİRME ALANI (SOL MENÜ ÜSTÜ) ---
# --- SEPET VE TOPLU İNDİRME ALANI (SOL MENÜ) ---
st.sidebar.header("🛒 İndirme Otomasyonu")
sepet_sayisi = len(st.session_state.download_cart)

if sepet_sayisi > 0:
    st.sidebar.info(f"Sepetinizde {sepet_sayisi} adet içerik var.")
    
    with st.sidebar.expander("Sepetteki İçerikler", expanded=False):
        for isim in st.session_state.download_cart.values():
            st.markdown(f"- {isim}")
            
    if st.sidebar.button("🗑️ Sepeti Boşalt"):
        st.session_state.download_cart = {}
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Otomatik İndirme Araçları")

    # 1. SEÇENEK: IDM İLE TAM OTOMASYON (Klasör ve İsimlendirme Destekli)
    bat_lines = ["@echo off", "echo IDM Otomatik Indirme Baslatiliyor...", ""]
    
    for url, isim in st.session_state.download_cart.items():
        # Windows klasör isimlerinde yasaklı karakterleri temizle (/, \, :, *, ?, ", <, >, |)
        guvenli_isim = re.sub(r'[\\/*?:"<>|]', '', isim).strip()
        
        # IDMan.exe'ye linki, kayıt klasörünü (/p) ve dosya adını (/f) parametre olarak gönder
        bat_lines.append(f'echo Indiriliyor: {guvenli_isim}')
        bat_lines.append(f'start "" "C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe" /d "{url}" /p "C:\\Filmler\\{guvenli_isim}" /f "{guvenli_isim}.ts" /a')
    
    bat_lines.append("")
    bat_lines.append("echo Tum indirmeler IDM sirasina eklendi!")
    bat_lines.append("pause")
    
    bat_content = "\n".join(bat_lines)
    
    st.sidebar.download_button(
        label="🟢 IDM Otomasyon Dosyasını İndir (.bat)",
        data=bat_content,
        file_name="IDM_Otomatik_Indir.bat",
        mime="application/x-bat",
        help="Bu bat dosyasını indirip çift tıkladığınızda klasörler oluşur ve IDM indirmeye başlar."
    )

    # 2. SEÇENEK: WINDOWS CMD İLE (Programsız) İNDİRME
    cmd_lines = ["@echo off", "echo Windows CMD ile Indirme Baslatiliyor...", ""]
    for url, isim in st.session_state.download_cart.items():
        guvenli_isim = re.sub(r'[\\/*?:"<>|]', '', isim).strip()
        cmd_lines.append(f'mkdir "C:\\Filmler\\{guvenli_isim}" 2>nul')
        cmd_lines.append(f'curl -o "C:\\Filmler\\{guvenli_isim}\\{guvenli_isim}.ts" "{url}"')
    
    cmd_lines.append("echo Indirme tamamlandi!")
    cmd_lines.append("pause")
    cmd_content = "\n".join(cmd_lines)

    st.sidebar.download_button(
        label="🖥️ CMD (Programsız) Otomasyon İndir (.bat)",
        data=cmd_content,
        file_name="CMD_Otomatik_Indir.bat",
        mime="application/x-bat",
        help="Bilgisayarınızda ek bir program yoksa, Windows kendi başına klasörleri açıp indirmeyi yapar."
    )
# --- DOSYA YÜKLEME VE FİLTRELEME ---
st.sidebar.header("📂 Dosya Yükleme")
uploaded_file = st.sidebar.file_uploader("M3U Dosyanızı Yükleyin", type=["m3u", "m3u8"])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    df = parse_m3u(content)
    
    st.sidebar.header("🔍 İçerik Filtreleme")
    categories = sorted(df['Kategori'].unique().tolist())
    selected_category = st.sidebar.selectbox("Kategori Seçin", ["Tümü"] + categories)
    search_query = st.sidebar.text_input("Film / Dizi veya Kanal Ara")
    
    if selected_category != "Tümü":
        df = df[df['Kategori'] == selected_category]
    if search_query:
        df = df[df['İsim'].str.contains(search_query, case=False, na=False)]

    st.subheader(f"Bulunan İçerik Sayısı: {len(df)}")
    
    display_limit = 100
    if len(df) > display_limit:
        st.warning(f"Performans için sadece ilk {display_limit} sonuç gösteriliyor.")
    
    cols = st.columns(4)
    
    for index, row in df.head(display_limit).reset_index(drop=True).iterrows():
        col = cols[index % 4]
        with col:
            try:
                st.image(row["Logo"], use_container_width=True)
            except Exception:
                st.image("https://via.placeholder.com/300x450.png?text=Gorsel+Yok", use_container_width=True)
            
            st.markdown(f'<div class="film-title">{row["İsim"]}</div>', unsafe_allow_html=True)
            
            # Seçim Kutucuğu (Sepete Ekle/Çıkar)
            url = row["URL"]
            isim = row["İsim"]
            is_checked = url in st.session_state.download_cart
            
            if st.checkbox("Sepete Ekle", value=is_checked, key=f"check_{index}"):
                st.session_state.download_cart[url] = isim
            else:
                if url in st.session_state.download_cart:
                    del st.session_state.download_cart[url]
            
            # HTML İle İzle ve Tekli İndir Butonları
            st.markdown(
                f"""
                <a href="{row['URL']}" target="_blank" class="action-btn watch-btn">
                    ▶ İzle
                </a>
                <a href="{row['URL']}" download class="action-btn download-btn">
                    📥 Tekli İndir
                </a>
                <hr/>
                """,
                unsafe_allow_html=True
            )
else:
    st.info("👈 Lütfen başlamak için sol menüden M3U dosyanızı yükleyin.")
