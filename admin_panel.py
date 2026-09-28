import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Başlatma (Güvenli Kontrol)
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        pass

db = firestore.client() if firebase_admin._apps else None

st.set_page_config(page_title="Medikal İhale Takip", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.is_admin = False

# Giriş Ekranı
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🛡️ Medikal İhale Takip</h2>", unsafe_allow_html=True)
    
    with st.form("login"):
        email = st.text_input("E-posta Adresiniz:")
        submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
        
        if submitted:
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
                    st.error("❌ Bu e-posta yetkili değil.")
            else:
                st.error("Veritabanı bağlantısı yok.")
else:
    if st.button("Çıkış Yap"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.divider()
    
    if st.session_state.is_admin:
        st.markdown("### 👑 Admin Paneli")
        tab1, tab2 = st.tabs(["İhale Ekle", "İhaleler"])
        with tab1:
            ikn = st.text_input("İKN:")
            kurum = st.text_input("Kurum:")
            tarih = st.text_input("Tarih:")
            ihale_adi = st.text_input("İhale Adı:")
            if st.button("Kaydet") and db and ikn:
                db.collection("tenders").document(ikn.replace("/", "_")).set({
                    "ikn": ikn, "kurum": kurum, "tarih": tarih, "ihale_adi": ihale_adi
                })
                st.success("Kaydedildi!")
        with tab2:
            if db:
                docs = db.collection("tenders").stream()
                data = [d.to_dict() for d in docs]
                if data: st.dataframe(pd.DataFrame(data))
    else:
        st.markdown("### 📋 Aktif İhaleler")
        if db:
            docs = db.collection("tenders").stream()
            for t in docs:
                val = t.to_dict()
                st.info(f"**{val.get('ikn')}** - {val.get('kurum')}\n\n{val.get('ihale_adi')}")
