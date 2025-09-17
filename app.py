import streamlit as st
from PIL import Image, ImageOps
import fitz  # PyMuPDF
import io

# --- CONFIGURATION & CONSTANTS (3DPI) ---

# --- NEW COORDINATES FOR THE VERTICAL LAYOUT PDF ---
# NOTE: These coordinates are for the new PDF format you provided.
FRONT_CROP_COORDS = (70, 2980, 2400, 3400) # The bottom-most part with the photo
BACK_CROP_COORDS = (70, 2450, 2400, 2980) # The part above it with the address

# Layout dimensions remain the same
CANVAS_SIZE = (2067, 1335)
SIDE_MARGIN = 55
TOP_BOTTOM_MARGIN = 115
VERTICAL_GAP = 100
CONTENT_WIDTH = CANVAS_SIZE[0] - (2 * SIDE_MARGIN)
CONTENT_HEIGHT = (CANVAS_SIZE[1] - (2 * TOP_BOTTOM_MARGIN) - VERTICAL_GAP) // 2
TARGET_RESIZE_DIM = (CONTENT_WIDTH, CONTENT_HEIGHT)
PASTE_POS_FRONT = (SIDE_MARGIN, TOP_BOTTOM_MARGIN)
PASTE_POS_BACK = (SIDE_MARGIN, TOP_BOTTOM_MARGIN + CONTENT_HEIGHT + VERTICAL_GAP)


def process_aadhaar(pdf_bytes, password):
    """
    Core processing function. Returns a tuple: (Image, message).
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf", password=password)
        if doc.is_encrypted and not doc.is_unlocked:
             return None, "Error: The password seems to be incorrect. Please double-check."
    except Exception as e:
        return None, f"Error: Could not open the PDF. It may be corrupted. Details: {str(e)}"

    try:
        pix = doc[0].get_pixmap(dpi=300)
        source_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Main image processing
        front_img = source_img.crop(FRONT_CROP_COORDS).resize(TARGET_RESIZE_DIM, Image.LANCZOS)
        back_img = source_img.crop(BACK_CROP_COORDS).resize(TARGET_RESIZE_DIM, Image.LANCZOS).rotate(180)
        
        front_img = ImageOps.expand(front_img, border=1, fill='black')
        back_img = ImageOps.expand(back_img, border=1, fill='black')

        canvas = Image.new("RGB", CANVAS_SIZE, "white")
        canvas.paste(front_img, PASTE_POS_FRONT)
        canvas.paste(back_img, PASTE_POS_BACK)
        
        return canvas, "Success"
    except Exception as e:
        return None, f"Error: Image processing failed. This usually means the PDF layout is different from the expected format. Crop coordinates may need adjustment."


# --- STREAMLIT USER INTERFACE ---

st.set_page_config(page_title="Aadhaar Card Converter", layout="wide")

st.title("📇 Aadhaar A4 to 4x6 Card Converter")
st.markdown("Upload your e-Aadhaar PDF, enter the password, and get a print-ready 4x6 inch card.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Your File")
    uploaded_file = st.file_uploader("Select your e-Aadhaar PDF", type="pdf")
    
    st.subheader("2. Enter Password")
    password = st.text_input("The password is usually the first 4 letters of your name (in CAPS) + your year of birth (YYYY)", type="password")
    
    generate_button = st.button("Generate Card", type="primary")

with col2:
    st.subheader("3. Your Result")
    if generate_button:
        if uploaded_file is not None and password:
            with st.spinner('Processing... This may take a moment.'):
                pdf_bytes = uploaded_file.getvalue()
                result_image, message = process_aadhaar(pdf_bytes, password)
            
            if result_image:
                st.success("✅ Card generated successfully!")
                st.image(result_image, caption="Your Print-Ready Card")
                
                img_byte_arr = io.BytesIO()
                result_image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                st.download_button(
                    label="Download Card as PNG",
                    data=img_byte_arr,
                    file_name="Aadhaar_Card_4x6.png",
                    mime="image/png"
                )
            else:
                st.error(message) 
        else:
            st.warning("⚠️ Please upload a file and enter the password first.")
