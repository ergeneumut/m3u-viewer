import streamlit as st
import pandas as pd
import re

# Sayfa Yapılandırması (Geniş ekran, özel başlık ve ikon)
st.set_page_config(page_title="🎬 VOD & IPTV Platformu", page_icon="🍿", layout="wide")

# CSS ile biraz daha estetik bir görünüm katalım
st.markdown("""
    <style>
    .film-title { font-size: 16px; font-weight: bold; margin-top: 10px; height: 50px; overflow: hidden; text-overflow: ellipsis; }
    .stButton>button { width: 100%; background-color: #E50914; color: white; border-radius: 5px; }
    .stButton>button:hover { background-color: #b20710; color: white; border-color: #b20710; }
    </style>
""", unsafe_allow_html=True)

st.title("🍿 Film, Dizi ve Canlı TV Merkezi")
st.markdown("İçeriklerinizi arayın, filtreleyin, izleyin veya cihazınıza tek tıkla indirin.")

# M3U Dosyasını Ayrıştıran Fonksiyon
@st.cache_data
def parse_m3u(file_content):
    lines = file_content.split('\n')
    data = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            # Kapak Fotoğrafını (Logo) Çek
            logo_match = re.search(r'tvg-logo="(.*?)"', line)
            logo = logo_match.group(1) if logo_match and logo_match.group(1) else "https://via.placeholder.com/300x450.png?text=Kapak+Yok"
            
            # Kategoriyi Çek
            cat_match = re.search(r'group-title="(.*?)"', line)
            category = cat_match.group(1).strip() if cat_match else "Diğer"
            
            # İçerik Adını Çek
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else "İsimsiz İçerik"
            
            # URL'yi Çek (Bir sonraki satır)
            url = ""
            if i + 1 < len(lines) and not lines[i+1].startswith('#'):
                url = lines[i+1].strip()
                i += 1
            
            data.append({"İsim": name, "Kategori": category, "Logo": logo, "URL": url})
        i += 1
    return pd.DataFrame(data)

# Sol Menü (Sidebar) - Dosya Yükleme ve Filtreleme
st.sidebar.header("📂 Dosya Yükleme")
uploaded_file = st.sidebar.file_uploader("M3U Dosyanızı Yükleyin", type=["m3u", "m3u8"])

if uploaded_file is not None:
    # Dosyayı oku ve DataFrame'e çevir
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    df = parse_m3u(content)
    
    st.sidebar.success("Dosya başarıyla yüklendi!")
    st.sidebar.markdown("---")
    
    # Arama ve Filtreleme
    st.sidebar.header("🔍 İçerik Filtreleme")
    
    # Kategori Seçici
    categories = sorted(df['Kategori'].unique().tolist())
    selected_category = st.sidebar.selectbox("Kategori Seçin", ["Tümü"] + categories)
    
    # Metin Araması
    search_query = st.sidebar.text_input("Film / Dizi veya Kanal Ara")
    
    # Filtreleri Uygula
    if selected_category != "Tümü":
        df = df[df['Kategori'] == selected_category]
    if search_query:
        df = df[df['İsim'].str.contains(search_query, case=False, na=False)]
        
    st.subheader(f"Bulunan İçerik Sayısı: {len(df)}")
    
    # Çok fazla veri arayüzü dondurmasın diye sayfalandırma/sınırlandırma (İlk 100 içeriği göster)
    display_limit = 100
    if len(df) > display_limit:
        st.warning(f"Performans için sadece ilk {display_limit} sonuç gösteriliyor. Lütfen aramanızı daraltın.")
    
    # Izgara (Grid) Yapısı ile İçerikleri Gösterme
    cols = st.columns(4) # Yan yana 4 içerik kartı
    
    for index, row in df.head(display_limit).reset_index(drop=True).iterrows():
        col = cols[index % 4]
        with col:
            # Kapak Fotoğrafı
            st.image(row["Logo"], use_container_width=True)
            
            # İçerik İsmi
            st.markdown(f'<div class="film-title">{row["İsim"]}</div>', unsafe_allow_html=True)
            
            # İzle Butonu
            if st.button("▶ İzle", key=f"watch_{index}"):
                try:
                    # Web tarayıcıları .mp4 veya webm formatlarını doğrudan oynatabilir
                    st.video(row["URL"])
                except Exception:
                    st.error("Bu yayın formatı tarayıcı içi oynatıcıyı desteklemiyor.")
            
            # İndir Butonu (.mkv gibi dosyalar telefonda tıklandığında direkt indirme başlatır)
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
    # Dosya yüklenmediğinde gösterilecek ekran
    st.info("👈 Lütfen başlamak için sol menüden **playlist_ruCZsxbJ (1).m3u** veya benzeri bir dosyanızı yükleyin.")
    st.image("https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=800&q=80", use_container_width=True)
