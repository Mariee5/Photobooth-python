import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import time
from io import BytesIO
import os
from pygame import mixer
from deepface import DeepFace
import pandas as pd
import plotly.express as px
from datetime import datetime

# Initialize session state for storing emotion data
if 'emotion_data' not in st.session_state:
    st.session_state.emotion_data = []

def apply_filter(image, filter_name):
    if filter_name == "Original":
        return image
    elif filter_name == "Sepia":
        width, height = image.size
        pixels = image.load()
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                r = int(r * 0.393 + g * 0.769 + b * 0.189)
                g = int(r * 0.349 + g * 0.686 + b * 0.168)
                b = int(r * 0.272 + g * 0.534 + b * 0.131)
                pixels[x, y] = (r, g, b)
        return image
    elif filter_name == "Vintage":
        image = ImageOps.grayscale(image)
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(0.5)
    elif filter_name == "Cool":
        image = ImageOps.grayscale(image)
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(1.5)
    elif filter_name == "Summer":
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.2)
    elif filter_name == "Dramatic":
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.5)
    return image

def analyze_face(image):
    try:
        result = DeepFace.analyze(image, actions=['emotion'], enforce_detection=False)  
        if isinstance(result, list):                      #result stored in 'result' which is a dictionary, so ifisinstance basically checks of the function can return a list of results(for multiple faces)
            result = result[0]
        return result
    except Exception as e:
        st.error(f"Could not detect face: {str(e)}")
        return None

def update_emotion_data(emotion_dict):
    emotion_data = {
        **emotion_dict
    }
    st.session_state.emotion_data.append(emotion_data)

def plot_emotions(emotions):
    plt.figure(figsize=(10, 6))
    plt.plot(emotions)
    plt.xlabel('Frame')
    plt.ylabel('Emotion Intensity')
    plt.title('Emotion Plot')
    st.pyplot(plt)

def add_frame(image, frame_width=50):
    width, height = image.size
    framed = Image.new('RGB', (width + 2*frame_width, height + 2*frame_width), (255, 255, 255))
    framed.paste(image, (frame_width, frame_width))
    return framed

def play_shutter_sound():
    try:
        mixer.init()
        mixer.music.load("shutter.mp3")
        mixer.music.play()
    except:
        pass

def upload_photos():
    # Photo upload section
    uploaded_files = st.file_uploader('Upload your photos', type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    if uploaded_files:
        photos = []
        analysis_results = []
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            photos.append(image)
            # Analyze face
            analysis = analyze_face(image)
            if analysis:
                analysis_results.append(analysis)
                update_emotion_data(analysis['emotion'])
        return photos, analysis_results
    return None, None

def create_photo_strip(photos):
    if not photos:
        return None
    
    padding = 20
    photo_height = photos[0].size[1]
    photo_width = photos[0].size[0]
    
    # Add extra space at bottom for date
    date_height = 40
    strip_height = (photo_height * len(photos)) + (padding * (len(photos) - 1)) + date_height
    
    strip = Image.new('RGB', (photo_width, strip_height), (255, 255, 255))
    
    # Add photos
    for i, photo in enumerate(photos):
        y_start = i * (photo_height + padding)
        y_end = y_start + photo_height
        strip.paste(photo, (0, y_start))
    
    # Add date at the bottom
    current_date = datetime.now().strftime("%B %d, %Y")
    font_size = 20
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text size and center it
    text_bbox = ImageDraw.Draw(strip).textbbox((0, 0), current_date, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (photo_width - text_width) // 2
    text_y = strip_height - date_height + 10
    
    ImageDraw.Draw(strip).text((text_x, text_y), current_date, fill=(100, 100, 100), font=font)
    
    return strip

def main():
    st.set_page_config(
        page_title="AI Photobooth",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Set dark theme and custom styles
    st.markdown("""
        <style>
        /* Dark theme */
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
        }
        
        [data-testid="stSidebar"] {
            background-color: #262730;
        }
        
        /* Text colors */
        h1, h2, h3, p, li, label, div {
            color: #ffffff !important;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            font-size: 20px;
            padding: 20px 40px;
            border-radius: 10px;
            border: none;
        }
        
        /* Sidebar text */
        .sidebar .sidebar-content {
            color: #ffffff;
        }
        
        /* Alert boxes */
        .stAlert {
            background-color: #262730;
            color: #ffffff;
        }
        
        /* Code blocks and other elements */
        code {
            color: #ff4b4b !important;
        }
        
        /* Links */
        a {
            color: #ff4b4b !important;
        }
        
        /* Dropdown and selectbox */
        .stSelectbox > div > div {
            background-color: #262730;
            color: #ffffff;
        }

        /* Grid styling */
        .stImage {
            margin: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📸 Marie's PhotoBooth!")
    st.header("Welcome and get your photostrip with your friends, family or just you yourself! in just 5 mins!")
    st.markdown("""
    ### Create your perfect photo strip with AI-powered features!
    
    Take 3 consecutive photos with:
    - Real-time emotion detection 🎭
    - Instagram-style filters ✨
    - Beautiful photo frame 🖼️
    
    ### Instructions:
    1. Select your preferred filter from the sidebar
    2. Click the "Start Photoshoot!" button
    3. Strike a pose during the countdown
    4. Watch for the "SMILE!" message - that's when the photo is taken!
    5. View your emotions analysis
    6. Download your photo strip when done
    """)
    
    # Sidebar options
    st.sidebar.title("Settings")
    black_white = st.sidebar.checkbox("Black & White Mode")
    filter_options = ["Original", "Sepia", "Vintage", "Cool", "Summer", "Dramatic"]
    selected_filter = st.sidebar.selectbox("Select Filter", filter_options)
    
    # Initialize session state for storing photos and emotions
    if 'photos_with_emotions' not in st.session_state:
        st.session_state.photos_with_emotions = []
    
    # Main interface with three columns
    col1, col2, col3 = st.columns([2, 0.1, 1])
    
    with col1:
        if st.button("Start Photoshoot! 📸"):
            photos, analysis_results = upload_photos()
            
            if photos and analysis_results:
                # Store photos with their emotions
                for photo, analysis in zip(photos, analysis_results):
                    emotions = analysis['emotion']
                    dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                    st.session_state.photos_with_emotions.append({
                        'photo': photo,
                        'emotion': dominant_emotion,
                    })
                
                st.write("Creating your photo strip...")
                photo_strip = create_photo_strip(photos)
                
                if photo_strip is not None:
                    st.write("Here's your photo strip! 🎉")
                    st.image(photo_strip, caption="Your Photo Strip")
                    
                    # Convert to PIL Image for saving
                    buf = BytesIO()
                    photo_strip.save(buf, format="PNG")
                    
                    # Download button
                    st.download_button(
                        label="Download Photo Strip 📥",
                        data=buf.getvalue(),
                        file_name="photo_strip.png",
                        mime="image/png"
                    )
    
    with col3:
        st.subheader("📊 Photo Gallery with Emotions")
        
        if st.session_state.photos_with_emotions:
            # Create a grid layout for photos
            for i in range(0, len(st.session_state.photos_with_emotions), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(st.session_state.photos_with_emotions):
                        item = st.session_state.photos_with_emotions[i + j]
                        with cols[j]:
                            # Resize photo for thumbnail
                            photo = item['photo'].copy()
                            photo.thumbnail((200, 200))
                            st.image(photo, caption=f"{item['emotion'].title()}")
        else:
            st.info("Take some photos to see them here!")
        
        if len(st.session_state.photos_with_emotions) > 0:
            if st.button("Clear Gallery"):
                st.session_state.photos_with_emotions = []
                st.session_state.emotion_data = []
                st.rerun()
        
        # Show emotion trends below the gallery
        st.subheader("Emotion Trends")
        if st.session_state.emotion_data:
            emotions = [list(emotion.values()) for emotion in st.session_state.emotion_data]
            plot_emotions([sum(x) for x in zip(*emotions)])

if __name__ == "__main__":
    main()
