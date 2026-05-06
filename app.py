import os
import cv2
import numpy as np
import pytesseract
import re
import difflib
from datetime import datetime
import streamlit as st

#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def preprocess_image(image_path):
    if isinstance(image_path, str):
        img = cv2.imread(image_path)
    else:
        img = image_path

    if img is None:
        raise FileNotFoundError("Image not found or could not be decoded.")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15)
    return thresh

def clean_text(text):
    text = text.replace("\n", "\n") 
    corrections = {
        r"Nef\s*Quanlity": "Net Quantity",
        r"Net Quanlity": "Net Quantity",
        r"Mig\s*Date": "Mfg Date",
        r"Exp Dale": "Exp Date",
        r"Manufactied\s*By": "Manufactured By",
        r"InIndia": "India",
        r"ind\. of alll tares": "",
        r"’": "'",
    }
    for pattern, repl in corrections.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text

def parse_date_mm_yy(date_str):
    date_str = date_str.strip()
    if re.match(r"^\d{5}$", date_str):
        mm = date_str[:2]
        yy = "20" + date_str[3:]
        return f"{yy}-{mm}-01"
    for fmt in ("%m/%y", "%d/%m/%y", "%m-%y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    return date_str

def fuzzy_match(keyword, text):
    """Return True if keyword is approximately present in text (handles OCR typos)."""
    words = text.split()
    match = difflib.get_close_matches(keyword, words, cutoff=0.7)
    return bool(match)

def extract_entities(text):
    entities = {
        "product_name": None,
        "mrp": None,
        "net_quantity": None,
        "country_of_origin": None,
        "manufactured_by": None,
        "mfg_date": None,
        "exp_date": None
    }

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        if re.search(r"(Net|Mfg|Exp|Manufactured|MRP|₹|Rs)", line, re.IGNORECASE):
            break
        if len(line) > 2:  
            entities["product_name"] = line
            break

    for line in lines:
        if fuzzy_match("Net", line) and fuzzy_match("Quantity", line):
            match = re.search(r"([\d\.]+\s*(pcs?|pack|ml|mg|g|kg|L)?)", line, re.IGNORECASE)
            if match:
                entities["net_quantity"] = match.group(1).strip()

        if "country" in line.lower():
            match = re.search(r"origin[:\s-]*([A-Za-z ]+)", line, re.IGNORECASE)
            if match:
                entities["country_of_origin"] = match.group(1).strip()

        if "manufactured" in line.lower():
            match = re.search(r"manufactured\s*by[:\s-]*(.+)", line, re.IGNORECASE)
            if match:
                entities["manufactured_by"] = match.group(1).strip()

    mrp_match = re.findall(r"[\d,]{3,}", text)
    if mrp_match:
        for num in mrp_match:
            try:
                n = int(num.replace(",", ""))
                if n > 10:
                    entities["mrp"] = float(n)
                    print(f"✅ MRP: {entities['mrp']}")
                    break
            except ValueError:
                continue

    for line in lines:
        date_matches = re.findall(r"\d{2}/\d{2}|\d{5}", line)
        if date_matches:
            if not entities["mfg_date"]:
                entities["mfg_date"] = parse_date_mm_yy(date_matches[0])
            elif not entities["exp_date"]:
                entities["exp_date"] = parse_date_mm_yy(date_matches[0])

    return entities

def extract_product_info(image_path):
    img = preprocess_image(image_path)
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=₹$Rs.0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,./:- '
    raw_text = pytesseract.image_to_string(img, config=custom_config)
    cleaned_text = clean_text(raw_text)
    entities = extract_entities(cleaned_text)
    return cleaned_text, entities

st.set_page_config(page_title="Product Info Extractor | OCR", page_icon="📸", layout="centered")

st.title("Product Info Extractor 📸")
st.write("Upload a product image and extract the label details with OCR.")

uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "bmp", "webp"])

if uploaded_file is not None:
    file_bytes = np.frombuffer(uploaded_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if image is None:
        st.error("The uploaded file could not be read as an image.")
    else:
        st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption=uploaded_file.name, use_container_width=True)

        if st.button("Extract Info"):
            with st.spinner("Extracting information, please wait..."):
                text, info = extract_product_info(image)

            st.subheader("Extracted Information")
            for key, value in info.items():
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value if value else 'Not found'}")

            with st.expander("Show OCR Text"):
                st.text_area("Cleaned OCR output", text, height=250)

            if info.get("mfg_date") or info.get("exp_date"):
                st.caption("Dates are normalized when OCR matches a recognizable month/year pattern.")
