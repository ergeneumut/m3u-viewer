import streamlit as st
import pandas as pd
import re
import math
import os
from urllib.parse import urlparse

# Sayfa Yapılandırması
st.set_page_config(page_title="🎬 VOD & IPTV Platformu", page_icon="🍿", layout="wide")

# Oturum Hafızası (Session State) Ayarları
if "download_cart" not in st.session_state:
    st.session_state.download_cart = {}
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "last_filter" not in st.session_state:
    st.session_state.last_filter = ("", "Tümü")

# Özel CSS Tasarımı
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
        font-size: 13px;
        transition: 0.3s;
    }
    .watch-btn { background-color: #E50914; border: 1px solid #E50914; }
    .watch-btn:hover { background-color: #b20710; }
    
    .potplayer-btn { background-color: #6a0dad; border: 1px solid #6a0dad; }
    .potplayer-btn:hover { background-color: #4b0082; }
    
    .download-btn { background-color: #28a745; border: 1px solid #28a745; }
    .download-btn:hover { background-color: #218838; }
    
    .stButton>button { width: 100%; font-weight: bold; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🍿 Film, Dizi ve Canlı TV Merkezi")
st.markdown("İçeriklerinizi arayın, çoklu ses seçeneği için PotPlayer'da izleyin veya toplu indirin.")

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

# URL'den orijinal dosya formatını algılayan fonksiyon
def get_file_extension(url):
    parsed_path = urlparse(url).path
    ext = os.path.splitext(parsed_path)[1]
    # Eğer geçerli bir uzantı bulursa (.mkv, .mp4, .ts) onu kullan, bulamazsa .mkv varsay
    if ext and len(ext) <= 5:
        return ext
    return ".mkv"

# --- SEPET VE TOPLU İNDİRME ALANI (SOL MENÜ) ---
st.sidebar.header("🛒 İndirme Otomasyonu")
sepet_sayisi = len(st.session_state.download_cart)

if sepet_sayisi > 0:
    st.sidebar.success(f"Sepetinizde {sepet_sayisi} adet içerik var.")
    
    with st.sidebar.expander("Sepetteki İçerikler", expanded=False):
        for isim in st.session_state.download_cart.values():
            st.markdown(f"- {isim}")
            
    if st.sidebar.button("🗑️ Sepeti Boşalt"):
        st.session_state.download_cart = {}
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Otomatik İndirme Araçları")

    # IDM Otomasyon Dosyası (Dinamik Uzantı)
    bat_lines = ["@echo off", "echo IDM Otomatik Indirme Baslatiliyor...", ""]
    for url, isim in st.session_state.download_cart.items():
        guvenli_isim = re.sub(r'[\\/*?:"<>|]', '', isim).strip()
        uzanti = get_file_extension(url) # Gerçek formatı bul
        
        bat_lines.append(f'echo Indiriliyor: {guvenli_isim}{uzanti}')
        bat_lines.append(f'start "" "C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe" /d "{url}" /p "C:\\Filmler\\{guvenli_isim}" /f "{guvenli_isim}{uzanti}" /a')
    
    bat_lines.append("")
    bat_lines.append("echo Tum indirmeler IDM sirasina eklendi!")
    bat_lines.append("pause")
    
    st.sidebar.download_button(
        label="🟢 IDM Otomasyon İndir (.bat)",
        data="\n".join(bat_lines),
        file_name="IDM_Otomatik_Indir.bat",
        mime="application/x-bat"
    )

    # CMD Otomasyon Dosyası (Dinamik Uzantı)
    cmd_lines = ["@echo off", "echo Windows CMD ile Indirme Baslatiliyor...", ""]
    for url, isim in st.session_state.download_cart.items():
        guvenli_isim = re.sub(r'[\\/*?:"<>|]', '', isim).strip()
        uzanti = get_file_extension(url) # Gerçek formatı bul
        
        cmd_lines.append(f'mkdir "C:\\Filmler\\{guvenli_isim}" 2>nul')
        cmd_lines.append(f'curl -o "C:\\Filmler\\{guvenli_isim}\\{guvenli_isim}{uzanti}" "{url}"')
    cmd_lines.append("pause")
    
    st.sidebar.download_button(
        label="🖥️ CMD Otomasyon İndir (.bat)",
        data="\n".join(cmd_lines),
        file_name="CMD_Otomatik_Indir.bat",
        mime="application/x-bat"
    )
else:
    st.sidebar.info("Sepetiniz şu an boş.")

st.sidebar.markdown("---")

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
    
    if (search_query, selected_category) != st.session_state.last_filter:
        st.session_state.current_page = 1
        st.session_state.last_filter = (search_query, selected_category)
    
    if selected_category != "Tümü":
        df = df[df['Kategori'] == selected_category]
    if search_query:
        df = df[df['İsim'].str.contains(search_query, case=False, na=False)]

    total_items = len(df)
    st.subheader(f"Bulunan İçerik Sayısı: {total_items}")
    
    # --- SAYFALANDIRMA (PAGINATION) SİSTEMİ ---
    items_per_page = 100
    total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
    
    if total_items > 0:
        col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
        with col_page2:
            st.session_state.current_page = st.number_input(
                f"Sayfa Seçin (Toplam: {total_pages})", 
                min_value=1, 
                max_value=total_pages, 
                value=st.session_state.current_page,
                step=1
            )
            
        st.markdown("---")

        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        df_page = df.iloc[start_idx:end_idx]
        
        cols = st.columns(4)
        
        for index, row in df_page.reset_index(drop=True).iterrows():
            col = cols[index % 4]
            with col:
                try:
                    st.image(row["Logo"], use_container_width=True)
                except Exception:
                    st.image("https://via.placeholder.com/300x450.png?text=Gorsel+Yok", use_container_width=True)
                
                st.markdown(f'<div class="film-title">{row["İsim"]}</div>', unsafe_allow_html=True)
                
                url = row["URL"]
                isim = row["İsim"]
                
                st.markdown(
                    f"""
                    <a href="{url}" target="_blank" class="action-btn watch-btn">
                        ▶ Tarayıcıda İzle
                    </a>
                    <a href="potplayer://{url}" class="action-btn potplayer-btn">
                        📺 PotPlayer'da Aç (Çift Ses)
                    </a>
                    <a href="{url}" download class="action-btn download-btn">
                        📥 Tekli İndir
                    </a>
                    """,
                    unsafe_allow_html=True
                )
                
                if url in st.session_state.download_cart:
                    if st.button("❌ Sepetten Çıkar", key=f"out_{hash(url)}", use_container_width=True):
                        del st.session_state.download_cart[url]
                        st.rerun() 
                else:
                    if st.button("🛒 Sepete Ekle", key=f"in_{hash(url)}", use_container_width=True):
                        st.session_state.download_cart[url] = isim
                        st.rerun() 
                        
                st.markdown("<hr/>", unsafe_allow_html=True)
    else:
        st.warning("Aradığınız kriterlere uygun içerik bulunamadı.")
else:
    st.info("👈 Lütfen başlamak için sol menüden M3U dosyanızı yükleyin.")
