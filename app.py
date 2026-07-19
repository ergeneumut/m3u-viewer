import streamlit as st
import pandas as pd
import re
import math
import os
from urllib.parse import urlparse

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="🎬 Film", page_icon="🍿", layout="wide")

# --- HAFIZA VE CALLBACK FONKSİYONLARI (Hata Çözümü) ---
# st.rerun() hatasını önlemek için butonların arka planda tetikleyeceği fonksiyonlar
if "download_cart" not in st.session_state:
    st.session_state.download_cart = {}
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "last_filter" not in st.session_state:
    st.session_state.last_filter = ("", "Tümü")

def add_to_cart(url, isim):
    st.session_state.download_cart[url] = isim

def remove_from_cart(url):
    if url in st.session_state.download_cart:
        del st.session_state.download_cart[url]

def clear_cart():
    st.session_state.download_cart.clear()

def select_all_filtered(filtered_df):
    for _, row in filtered_df.iterrows():
        st.session_state.download_cart[row["URL"]] = row["İsim"]

def deselect_all_filtered(filtered_df):
    for _, row in filtered_df.iterrows():
        if row["URL"] in st.session_state.download_cart:
            del st.session_state.download_cart[row["URL"]]

# --- CSS TASARIMI ---
st.markdown("""
    <style>
    .film-title { font-size: 16px; font-weight: bold; margin-top: 10px; height: 50px; overflow: hidden; text-overflow: ellipsis; }
    .action-btn {
        display: block; width: 100%; text-align: center; padding: 8px; border-radius: 5px;
        margin-top: 5px; text-decoration: none !important; font-weight: bold; color: white !important; font-size: 13px; transition: 0.3s;
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

st.title("🍿 Film")

# --- M3U DOSYA ÇÖZÜCÜ ---
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

def get_file_extension(url):
    parsed_path = urlparse(url).path
    ext = os.path.splitext(parsed_path)[1]
    if ext and len(ext) <= 5:
        return ext
    return ".mkv"

# --- SOL MENÜ (DOSYA YÜKLEME VE FİLTRE) ---
st.sidebar.header("📂 Dosya Yükleme")

uploaded_file = st.sidebar.file_uploader("M3U Dosyanızı Yükleyin", type=["m3u", "m3u8"])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    df = parse_m3u(content)
    
    st.sidebar.header("🔍 İçerik Filtreleme")
    categories = sorted(df['Kategori'].unique().tolist())
    selected_category = st.sidebar.selectbox("Kategori Seçin", ["Tümü"] + categories)
    search_query = st.sidebar.text_input("Film/Kanal Ara")
    
    if (search_query, selected_category) != st.session_state.last_filter:
        st.session_state.current_page = 1
        st.session_state.last_filter = (search_query, selected_category)
    
    if selected_category != "Tümü":
        df = df[df['Kategori'] == selected_category]
    if search_query:
        df = df[df['İsim'].str.contains(search_query, case=False, na=False)]

    total_items = len(df)
    
    # --- ANA EKRAN SEKMELERİ (TABS) ---
    tab1, tab2 = st.tabs(["🖼️ Katalog Görünümü", "📄 Yazılı Liste)"])
    
    # === SEKME 1: AFİŞLİ GÖRÜNÜM ===
    with tab1:
        st.subheader(f"İçerik Sayısı: {total_items}")
        items_per_page = 100
        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        
        if total_items > 0:
            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page2:
                st.session_state.current_page = st.number_input(
                    f"Sayfa Seçin (Toplam: {total_pages})", min_value=1, max_value=total_pages, value=st.session_state.current_page, step=1
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
                    
                    st.markdown(
                        f"""
                        <a href="vlc://{url}" class="action-btn potplayer-btn">📺 VLC'de Aç</a>
                        <a href="{url}" download class="action-btn download-btn">📥 İndir</a>
                        """, unsafe_allow_html=True
                    )
                    
                    # Güncellenmiş Callback Butonları (Yenileme yapmaz, hafızayı silmez)
                    if url in st.session_state.download_cart:
                        st.button("❌ Sepetten Çıkar", key=f"out_{hash(url)}", use_container_width=True, on_click=remove_from_cart, args=(url,))
                    else:
                        st.button("🛒 İndirme Sepetine Ekle", key=f"in_{hash(url)}", use_container_width=True, on_click=add_to_cart, args=(url, row["İsim"]))
                            
                    st.markdown("<hr/>", unsafe_allow_html=True)
        else:
            st.warning("Aradığınız kriterlere uygun içerik bulunamadı.")

    # === SEKME 2: YAZILI VE TOPLU SEÇİM LİSTESİ ===
    with tab2:
        st.subheader("📄 Kategori Bazlı Liste")
        st.markdown("Seçtiğiniz kategoriye (veya aramaya) ait tüm filmleri buradan topluca seçebilirsiniz.")
        
        # Tümünü Seç ve Kaldır Butonları
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.button("✅ Bu Sayfadaki Tüm İçerikleri Seç", use_container_width=True, on_click=select_all_filtered, args=(df,))
        with col_btn2:
            st.button("❌ Bu Sayfadaki Seçimleri Kaldır", use_container_width=True, on_click=deselect_all_filtered, args=(df,))
        
        # Data Editor İçin Özel Veri Hazırlığı
        df_list = df[['Kategori', 'İsim', 'URL']].copy()
        df_list.insert(0, "Seçili", df_list['URL'].map(lambda x: x in st.session_state.download_cart))
        
        # Tablo Render (Kutucukları içerir)
        edited_df = st.data_editor(
            df_list,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seçili": st.column_config.CheckboxColumn("Seç", default=False),
                "URL": st.column_config.LinkColumn("Yayın Linki")
            },
            disabled=["Kategori", "İsim", "URL"],
            height=600,
            key=f"editor_{hash(search_query + selected_category)}"
        )
        
        # Tablodaki manuel tıklamaları sepete eşitleme
        for _, row in edited_df.iterrows():
            url = row['URL']
            if row['Seçili'] and url not in st.session_state.download_cart:
                st.session_state.download_cart[url] = row['İsim']
            elif not row['Seçili'] and url in st.session_state.download_cart:
                del st.session_state.download_cart[url]

    # --- SOL MENÜ (SEPET VE İNDİRME ALANI) EN SON YÜKLENİR ---
    st.sidebar.markdown("---")
    st.sidebar.header("🛒 İndirme Sepeti")
    sepet_sayisi = len(st.session_state.download_cart)

    if sepet_sayisi > 0:
        st.sidebar.success(f"Sepetinizde {sepet_sayisi} adet içerik var.")
        
        with st.sidebar.expander("Sepetteki İçerikler", expanded=False):
            for isim in st.session_state.download_cart.values():
                st.markdown(f"- {isim}")
                
        # Güncellenmiş Callback ile Sepeti Boşaltma
        st.sidebar.button("🗑️ Sepeti Boşalt", use_container_width=True, on_click=clear_cart)
            
        st.sidebar.markdown("---")
        st.sidebar.subheader("🚀 İndirme Araçları")

        # 1. Link (.txt) Dosyası İndirme
        txt_content = "\n".join(st.session_state.download_cart.keys())
        st.sidebar.download_button(
            label="📝 Linkleri İndir (.txt)",
            data=txt_content,
            file_name="secili_mkv_linkleri.txt",
            mime="text/plain",
            help="Seçtiğiniz tüm filmlerin indirme linklerini alt alta text dosyası olarak verir."
        )

        # 2. IDM İndirme
        bat_lines = ["@echo off", "echo IDM Otomatik Indirme Baslatiliyor...", ""]
        for url, isim in st.session_state.download_cart.items():
            guvenli_isim = re.sub(r'[\\/*?:"<>|]', '', isim).strip()
            uzanti = get_file_extension(url)
            bat_lines.append(f'start "" "C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe" /d "{url}" /p "C:\\Filmler\\{guvenli_isim}" /f "{guvenli_isim}{uzanti}" /a')
        
        st.sidebar.download_button(
            label="IDM İndirme",
            data="\n".join(bat_lines),
            file_name="IDD_download_job.bat",
            mime="application/x-bat"
        )
    else:
        st.sidebar.info("Sepetiniz şu an boş.")
else:
    st.info("👈 Lütfen başlamak için sol menüden M3U dosyanızı yükleyin.")
