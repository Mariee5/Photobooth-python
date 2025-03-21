import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import time
from io import BytesIO
import os
from pygame import mixer
from deepface import DeepFace
import pandas as pd
import plotly.express as px
from datetime import datetime
from skimage import filters, exposure
import matplotlib.pyplot as plt

# Initialize session state for storing emotion data
if 'emotion_data' not in st.session_state:
    st.session_state.emotion_data = []

def apply_filter(image, filter_name):
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    
    img_float = image.astype(float) / 255.0
    
    if filter_name == "Original":
        return image
    elif filter_name == "Sepia":
        sepia_filter = np.array([[0.393, 0.769, 0.189],
                               [0.349, 0.686, 0.168],
                               [0.272, 0.534, 0.131]])
        sepia_img = cv2.transform(image, sepia_filter)
        sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
        return sepia_img
    elif filter_name == "Vintage":
        vintage = cv2.applyColorMap(image, cv2.COLORMAP_BONE)
        return vintage
    elif filter_name == "Cool":
        cool = cv2.applyColorMap(image, cv2.COLORMAP_COOL)
        return cool
    elif filter_name == "Summer":
        summer = exposure.adjust_gamma(img_float, 1.2)
        summer = exposure.adjust_sigmoid(summer, cutoff=0.5, gain=10)
        return (summer * 255).astype(np.uint8)
    elif filter_name == "Dramatic":
        dramatic = exposure.adjust_gamma(img_float, 2.0)
        dramatic = filters.unsharp_mask(dramatic, radius=2, amount=2)
        return (dramatic * 255).astype(np.uint8)
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
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    
    h, w = image.shape[:2]
    framed = np.ones((h + 2*frame_width, w + 2*frame_width, 3), dtype=np.uint8) * 255
    framed[frame_width:h+frame_width, frame_width:w+frame_width] = image
    return framed

def play_shutter_sound():
    try:
        mixer.init()
        mixer.music.load("shutter.mp3")
        mixer.music.play()
    except:
        pass

def capture_photos(num_photos=3, delay=3, black_white=False, selected_filter="Original"):
    photos = []
    analysis_results = []
    cap = st.camera_input('Take your photos!')
    if cap is not None:
        preview_placeholder = st.empty()
        status_placeholder = st.empty()
        preview_placeholder.image(cap, caption='Preview')
        status_placeholder.success('Photo captured!')
        
        # Analyze face
        analysis = analyze_face(cap)
        if analysis:
            analysis_results.append(analysis)
            update_emotion_data(analysis['emotion'])
        
        if black_white:
            cap = cv2.cvtColor(cap, cv2.COLOR_RGB2GRAY)
            cap = cv2.cvtColor(cap, cv2.COLOR_GRAY2RGB)
        
        # Apply selected filter
        cap = apply_filter(cap, selected_filter)
        
        # Add frame
        cap = add_frame(cap)
        play_shutter_sound()
        
        photos.append(cap)
        
        if analysis:
            emotions = analysis['emotion']
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
            status_placeholder.info(f"Dominant emotion in photo: {dominant_emotion}")
        
        return photos, analysis_results
    else:
        return None, None

def create_photo_strip(photos):
    if not photos:
        return None
    
    padding = 20
    photo_height = photos[0].shape[0]
    photo_width = photos[0].shape[1]
    
    # Add extra space at bottom for date
    date_height = 40
    strip_height = (photo_height * len(photos)) + (padding * (len(photos) - 1)) + date_height
    
    strip = np.ones((strip_height, photo_width, 3), dtype=np.uint8) * 255
    
    # Add photos
    for i, photo in enumerate(photos):
        y_start = i * (photo_height + padding)
        y_end = y_start + photo_height
        strip[y_start:y_end] = photo
    
    # Convert to PIL Image to add date text
    strip_pil = Image.fromarray(strip)
    draw = ImageDraw.Draw(strip_pil)
    
    # Add date at the bottom
    current_date = datetime.now().strftime("%B %d, %Y")
    font_size = 20
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text size and center it
    text_bbox = draw.textbbox((0, 0), current_date, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (photo_width - text_width) // 2
    text_y = strip_height - date_height + 10
    
    draw.text((text_x, text_y), current_date, fill=(100, 100, 100), font=font)
    
    return np.array(strip_pil)

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
            photos, analysis_results = capture_photos(black_white=black_white, selected_filter=selected_filter)
            
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
                    pil_image = Image.fromarray(photo_strip)
                    buf = BytesIO()
                    pil_image.save(buf, format="PNG")
                    
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
                            photo = Image.fromarray(item['photo'])
                            photo.thumbnail((200, 200))
                            st.image(np.array(photo), caption=f"{item['emotion'].title()}")
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
