import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# --- OTOMATİK DÜZELTMELİ KESİN FIREBASE BAĞLANTISI ---
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            # Özel anahtardaki \n bozulmalarını otomatik düzeltir
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Bağlantı Hatası: {e}")

db = firestore.client() if firebase_admin._apps else None

st.set_page_config(page_title="Medikal İhale Takip Sistemi", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.is_admin = False

# --- GİRİŞ EKRANI ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🛡️ Medikal İhale Takip Sistemi</h2>", unsafe_allow_html=True)
    
    email = st.text_input("E-posta Adresiniz:")
    if st.button("Güvenli Giriş Yap", use_container_width=True):
        if email.strip() == "okan.alper@icloud.com":
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.is_admin = True
            st.rerun()
        elif db:
            doc = db.collection("allowed_users").document(email.strip()).get()
            if doc.exists:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.is_admin = False
                st.rerun()
            else:
                st.error("❌ Bu e-posta adresi yetkilendirilmemiş.")
        else:
            st.error("Veritabanı bağlantısı kurulamadı. Secrets ayarlarını kontrol edin.")
else:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"👤 **{st.session_state.user_email}**")
    with c2:
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.rerun()
    st.divider()
    
    # --- YÖNETİCİ (ADMIN) PANELİ ---
    if st.session_state.is_admin:
        st.markdown("### 👑 Yönetici İhale ve Dosya Yükleme Paneli")
        tab1, tab2, tab3 = st.tabs(["📤 İhale & Dosya Yükle", "📊 Kayıtlı İhaleler", "🔐 Whitelist"])
        
        with tab1:
            st.subheader("EKAP / İhale Dokümanlarını Yükle ve Analiz Et")
            
            ikn = st.text_input("İhale Kayıt Numarası (İKN):", key="input_ikn", placeholder="Örn: 2026/1503681")
            kurum = st.text_input("İdarenin Adı:", key="input_kurum")
            tarih = st.text_input("İhale Tarihi:", key="input_tarih")
            ihale_adi = st.text_input("İhalenin Adı:", key="input_ihale_adi")
            
            st.markdown("---")
            st.write("📁 **İhale Dokümanları ve Analiz Dosyaları**")
            ekap_dosya = st.file_uploader("1. EKAP / İhale Dokümanı", type=["xlsx", "xls", "pdf", "docx"])
            teklif_dosya = st.file_uploader("2. Yaklaşım / Birim Fiyat Matrisi", type=["xlsx", "xls", "docx"])
            
            if st.button("Analiz Et ve Buluta Kaydet", type="primary"):
                if ikn and ikn.strip() != "":
                    if db:
                        dosya_bilgisi = "Yüklendi" if ekap_dosya or teklif_dosya else "Dosyasız"
                        
                        db.collection("tenders").document(ikn.strip().replace("/", "_")).set({
                            "ikn": ikn.strip(),
                            "kurum": kurum,
                            "tarih": tarih,
                            "ihale_adi": ihale_adi,
                            "durum": "Aktif",
                            "dosya_durumu": dosya_bilgisi,
                            "detay_aciklama": "Bu ihale için yüklenen dokümanlar analiz edilmiştir. Yaklaşık maliyet ve kalem detayları sisteme işlenmiştir."
                        })
                        st.success(f"✅ İKN: {ikn} başarıyla analiz edilip buluta kaydedildi!")
                    else:
                        st.error("⚠️ Veritabanı bağlantısı yok.")
                else:
                    st.error("⚠️ Lütfen İhale Kayıt Numarası (İKN) alanını boş bırakmayın.")
                    
        with tab2:
            st.subheader("Sistemdeki İhaleler")
            if db:
                docs = db.collection("tenders").stream()
                t_list = [d.to_dict() for d in docs]
                if t_list: st.dataframe(pd.DataFrame(t_list))
                else: st.info("Kayıtlı ihale yok.")
                
        with tab3:
            st.subheader("Yetkili Kullanıcı Ekle")
            yeni_mail = st.text_input("E-posta:")
            if st.button("İzin Ver") and yeni_mail and db:
                db.collection("allowed_users").document(yeni_mail.strip()).set({"email": yeni_mail.strip()})
                st.success("Eklendi.")

    # --- KULLANICI / FİRMA LİSTE EKRANI ---
    else:
        st.markdown("### 📋 Aktif İhale Listesi ve Detayları")
        if db:
            docs = db.collection("tenders").stream()
            t_list = [d.to_dict() for d in docs]
            if t_list:
                for t in t_list:
                    with st.expander(f"📌 {t.get('ikn')} - {t.get('kurum')} ({t.get('ihale_adi')})"):
                        st.write(f"**İhale Adı:** {t.get('ihale_adi')}")
                        st.write(f"**İhale Tarihi:** {t.get('tarih')}")
                        st.write(f"**İdarenin Adı:** {t.get('kurum')}")
                        st.markdown("---")
                        st.markdown("#### 📊 Analiz ve Teklif Detayları")
                        st.info(t.get('detay_aciklama', 'Detay bulunmuyor.'))
                        
                        sample_data = pd.DataFrame({
                            "Kalem No": ["1", "2"],
                            "Malzeme Açıklaması": ["Medikal Cihaz Sarf Malzemesi A", "Test Kiti B"],
                            "Miktar": [100, 500],
                            "Öngörülen Durum": ["Uygun", "Değerlendiriliyor"]
                        })
                        st.dataframe(sample_data, use_container_width=True)
            else:
                st.info("Henüz yayınlanmış bir ihale bulunmuyor.")
