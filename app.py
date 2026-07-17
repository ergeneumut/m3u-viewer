import streamlit as st
import pandas as pd
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="🎬 VOD & IPTV Platformu", page_icon="🍿", layout="wide")

st.markdown("""
    <style>
    .film-title { font-size: 16px; font-weight: bold; margin-top: 10px; height: 50px; overflow: hidden; text-overflow: ellipsis; }
    .stButton>button { width: 100%; background-color: #E50914; color: white; border-radius: 5px; }
    .stButton>button:hover { background-color: #b20710; color: white; border-color: #b20710; }
    </style>
""", unsafe_allow_html=True)

st.title("🍿 Film, Dizi ve Canlı TV Merkezi")
st.markdown("İçeriklerinizi arayın, filtreleyin, izleyin veya cihazınıza tek tıkla indirin.")

@st.cache_data
def parse_m3u(file_content):
    lines = file_content.split('\n')
    data = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            # Kapak Fotoğrafını (Logo) Çek ve Doğrula
            logo_match = re.search(r'tvg-logo="(.*?)"', line)
            logo = logo_match.group(1).strip() if logo_match and logo_match.group(1) else ""
            
            # Eğer logo bir web adresi değilse varsayılan görseli ata
            if not logo.startswith("http"):
                logo = "https://via.placeholder.com/300x450.png?text=Kapak+Yok"
            
            # Kategoriyi Çek
            cat_match = re.search(r'group-title="(.*?)"', line)
            category = cat_match.group(1).strip() if cat_match else "Diğer"
            
            # İçerik Adını Çek
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else "İsimsiz İçerik"
            
            # URL'yi Çek
            url = ""
            if i + 1 < len(lines) and not lines[i+1].startswith('#'):
                url = lines[i+1].strip()
                i += 1
            
            data.append({"İsim": name, "Kategori": category, "Logo": logo, "URL": url})
        i += 1
    return pd.DataFrame(data)

# Sol Menü (Sidebar)
st.sidebar.header("📂 Dosya Yükleme")
uploaded_file = st.sidebar.file_uploader("M3U Dosyanızı Yükleyin", type=["m3u", "m3u8"])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    df = parse_m3u(content)
    
    st.sidebar.success("Dosya başarıyla yüklendi!")
    st.sidebar.markdown("---")
    
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
        st.warning(f"Performans için sadece ilk {display_limit} sonuç gösteriliyor. Lütfen aramanızı daraltın.")
    
    cols = st.columns(4)
    
    for index, row in df.head(display_limit).reset_index(drop=True).iterrows():
        col = cols[index % 4]
        with col:
            # GÖRSEL YÜKLEME (Hata Yakalama Ekli)
            try:
                st.image(row["Logo"], use_container_width=True)
            except Exception:
                st.image("https://via.placeholder.com/300x450.png?text=Gorsel+Hatasi", use_container_width=True)
            
            st.markdown(f'<div class="film-title">{row["İsim"]}</div>', unsafe_allow_html=True)
            
            if st.button("▶ İzle", key=f"watch_{index}"):
                try:
                    st.video(row["URL"])
                except Exception:
                    st.error("Bu yayın formatı tarayıcı içi oynatıcıyı desteklemiyor.")
            
            st.markdown(
                f"""
                <a href="{row['URL']}" download target="_blank" style="text-decoration: none;">
                    <div style="background-color: #28a745; color: white; text-align: center; padding: 8px; border-radius: 5px; margin-top: 5px;">
                        📥 Cihaza İndir
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )
            st.markdown("<hr/>", unsafe_allow_html=True)
else:
    st.info("👈 Lütfen başlamak için sol menüden M3U dosyanızı yükleyin.")
    st.image("https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=800&q=80", use_container_width=True)
