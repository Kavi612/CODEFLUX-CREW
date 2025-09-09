import streamlit as st
import speech_recognition as sr
from PIL import Image
import pytesseract

from utils.check_prescription import check_prescription
from utils.granite_parser import parse_prescription_with_granite

# ---------------- Streamlit Config ----------------
st.set_page_config(page_title="GuardianRx", page_icon="💊", layout="centered")
st.title("💙 GuardianRx — AI Prescription Guardian")
st.caption("⚠️ Demo app — not medical advice.")

# ---------- Patient Info ----------
st.subheader("👤 Patient Information")
age = st.number_input("Age", min_value=0, max_value=120, value=30)
gender = st.radio("Gender", ("Male", "Female", "Other"))

# ---------- Input Selection ----------
input_type = st.radio("Select input type", ("Text", "Voice", "Image"))
prescription_text = ""

if input_type == "Text":
    prescription_text = st.text_area(
        "📝 Enter Prescription",
        placeholder="e.g., Paracetamol 1000 mg every 6 hours for 5 days + Warfarin 5 mg once daily"
    )

elif input_type == "Voice":
    st.subheader("🎤 Voice Input")
    if st.button("Start Recording"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎙️ Listening... please speak clearly.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        try:
            prescription_text = recognizer.recognize_google(audio)
            st.success("✅ Transcription complete!")
            st.code(prescription_text)
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio.")
        except sr.RequestError as e:
            st.error(f"API error: {e}")

elif input_type == "Image":
    uploaded_image = st.file_uploader("📸 Upload Prescription Image", type=['png', 'jpg', 'jpeg'])
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        prescription_text = pytesseract.image_to_string(image)
        st.text_area("Extracted Text", prescription_text)

# ---------- Analyze ----------
if st.button("Analyze"):
    if prescription_text.strip():
        # Step 1: Parse prescription
        st.info("⏳ Parsing prescription...")
        parsed = parse_prescription_with_granite(prescription_text)
        st.json(parsed)

        # Step 2: Safety checks
        st.info("⏳ Running safety checks...")
        result = check_prescription(prescription_text, age)

        # Combos
        if result["harmful_combos"]:
            st.subheader("🔥 Harmful Combos")
            for d1, d2, why, sev in result["harmful_combos"]:
                st.error(f"{d1} + {d2} → {why} (Severity: {sev})")
        else:
            st.success("No harmful combos ✅")

        # Dosage
        st.subheader("💊 Dosage Check")
        for d in result["dosage_checks"]:
            if d["status"] == "unsafe":
                st.error(f"{d['drug']} → {d['explanation']}")
            elif d["status"] == "safe":
                st.success(f"{d['drug']} → {d['explanation']}")
            else:
                st.warning(f"{d['drug']} → {d['explanation']}")

        # Food advice
        st.subheader("🍽️ Food Advice")
        for drug, tips in result["food_advice"]:
            if tips["avoid"]:
                st.warning(f"{drug}: Avoid {', '.join(tips['avoid'])}")

        # Mechanisms
        st.subheader("⚙️ Mechanisms")
        for drug, mech in result["mechanisms"]:
            st.caption(f"{drug} → {mech}")

        # Score
        st.subheader("📊 Safety Score")
        st.progress(result["safety_score"] / 100)
        st.write(f"Overall safety: {result['safety_score']}%")
    else:
        st.error("❌ Please input a prescription first.")
