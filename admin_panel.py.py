import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- 1. FIREBASE BAĞLANTI (BULUT & LOKAL UYUMLU) ---
if not firebase_admin._apps:
    try:
        # Önce Streamlit Cloud Secrets kontrolü, yoksa lokal dosya
        if "firebase" in st.secrets:
            secret_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(secret_dict)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        pass

db = firestore.client() if firebase_admin._apps else None

st.set_page_config(page_title="Medikal İhale Takip Sistemi", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.is_admin = False

# --- 2. GİRİŞ EKRANI ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🛡️ Medikal İhale Takip Sistemi</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Güvenli Bulut İhale ve Analiz Platformu</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        email_input = st.text_input("iCloud / E-posta Adresiniz:")
        submitted = st.form_submit_button("Güvenli Giriş Yap", use_container_width=True)
        
        if submitted:
            if email_input.strip() == "okan.alper@icloud.com":
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.session_state.is_admin = True
                st.rerun()
            elif db:
                try:
                    doc = db.collection("allowed_users").document(email_input.strip()).get()
                    if doc.exists:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email_input
                        st.session_state.is_admin = False
                        st.rerun()
                    else:
                        st.error("❌ Bu e-posta adresi sistemde yetkilendirilmemiş!")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")
            else:
                st.error("Veritabanı bağlantısı kurulamadı.")
                
# --- 3. SİSTEM GİRİŞİ BAŞARILI ---
else:
    col_u1, col_u2 = st.columns([3, 1])
    with col_u1:
        st.write(f"👤 **{st.session_state.user_email}** olarak giriş yapıldı.")
    with col_u2:
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
            
    st.divider()

    if st.session_state.is_admin:
        st.markdown("### 👑 Yönetici (Admin) Kontrol Paneli")
        tab1, tab2, tab3 = st.tabs(["📤 İhale Yükle", "📊 Aktif İhaleler", "🔐 Whitelist Yönetimi"])
        
        with tab1:
            st.subheader("Buluta Yeni İhale İşle")
            ikn = st.text_input("İhale Kayıt Numarası (İKN):", placeholder="Örn: 2026/1503681")
            kurum = st.text_input("İdarenin Adı:", placeholder="Örn: BURSA İL SAĞLIK MÜDÜRLÜĞÜ")
            tarih = st.text_input("İhale Tarihi:", placeholder="Örn: 28.09.2026")
            ihale_adi = st.text_input("İhalenin Adı:")
            
            if st.button("Buluta Kaydet", type="primary"):
                if ikn and db:
                    db.collection("tenders").document(ikn.replace("/", "_")).set({
                        "ikn": ikn, "kurum": kurum, "tarih": tarih, "ihale_adi": ihale_adi, "durum": "Yayında"
                    })
                    st.success(f"✅ {ikn} başarıyla buluta işlendi!")
                    
        with tab2:
            st.subheader("Sistemdeki İhaleler")
            if db:
                docs = db.collection("tenders").stream()
                t_list = [d.to_dict() for d in docs]
                if t_list: st.dataframe(pd.DataFrame(t_list), use_container_width=True)
                else: st.info("Kayıtlı ihale yok.")
                
        with tab3:
            st.subheader("İzinli Kullanıcı Ekle (Whitelist)")
            new_mail = st.text_input("E-posta Adresi:")
            if st.button("Erişim İzni Ver"):
                if new_mail and db:
                    db.collection("allowed_users").document(new_mail.strip()).set({"email": new_mail.strip()})
                    st.success(f"✅ {new_mail} eklendi.")
            
            st.write("Mevcut İzinli Liste:")
            if db:
                u_docs = db.collection("allowed_users").stream()
                u_list = [u.to_dict() for u in u_docs]
                if u_list: st.dataframe(pd.DataFrame(u_list), use_container_width=True)

    else:
        st.markdown("### 📋 Güncel İhale Listesi")
        if db:
            docs = db.collection("tenders").stream()
            t_list = [d.to_dict() for d in docs]
            if t_list:
                for t in t_list:
                    with st.expander(f"📌 {t.get('ikn')} - {t.get('kurum')}"):
                        st.write(f"**İhale Adı:** {t.get('ihale_adi')}")
                        st.write(f"**İhale Tarihi:** {t.get('ttarikh', t.get('tarih'))}")
                        st.markdown("---")
                        st.info("Detaylı teklif matrisi bu alanda listeleniyor.")
            else:
                st.info("Henüz yayınlanmış bir ihale bulunmuyor.")