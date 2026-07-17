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
st.sidebar.header("🛒 İndirme Sepeti")
sepet_sayisi = len(st.session_state.download_cart)

if sepet_sayisi > 0:
    st.sidebar.info(f"Sepetinizde {sepet_sayisi} adet içerik var.")
    
    # Seçili içeriklerin isimlerini göster
    with st.sidebar.expander("Sepetteki İçerikler", expanded=False):
        for isim in st.session_state.download_cart.values():
            st.markdown(f"- {isim}")
            
    if st.sidebar.button("🗑️ Sepeti Boşalt"):
        st.session_state.download_cart = {}
        st.rerun()
        
    # Linkleri birleştirip txt formatına dönüştür
    linkler_metni = "\n".join(st.session_state.download_cart.keys())
    
    st.sidebar.download_button(
        label="📥 qBittorrent/IDM İçin Linkleri İndir (.txt)",
        data=linkler_metni,
        file_name="toplu_indirme_listesi.txt",
        mime="text/plain",
        help="İndirdiğiniz bu txt dosyasının içindeki linkleri kopyalayıp qBittorrent veya IDM'ye yapıştırabilirsiniz."
    )
else:
    st.sidebar.write("Sepetiniz boş. Filmlerin altındaki kutucukları işaretleyerek listeye ekleyebilirsiniz.")

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
