# Product Info Extractor

An OCR-powered document intelligence system that extracts structured product information from scanned labels and images using Python, OpenCV, and Tesseract OCR.

## Features

- OCR-based text extraction
- Image preprocessing using OpenCV
- Product information extraction
- MRP detection
- Manufacturing & expiry date extraction
- Manufacturer details extraction
- Fuzzy text matching for OCR correction
- Structured output generation
- Flask-based web application

---

## Tech Stack

- Python
- Flask
- OpenCV
- Tesseract OCR
- Regex
- NumPy
- HTML/CSS

---

## Project Workflow

1. Upload product label image
2. Preprocess image using OpenCV
3. Extract text using Tesseract OCR
4. Clean noisy OCR text
5. Extract structured entities
6. Display extracted product information

---

## Extracted Information

The system can extract:

- Product Name
- MRP
- Net Quantity
- Manufacturing Date
- Expiry Date
- Manufacturer Details
- Country of Origin

---

## Folder Structure

```bash
product-info-extractor/
│
├── app.py
├── requirements.txt
├── README.md
