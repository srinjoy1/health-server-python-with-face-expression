import pandas as pd
import streamlit as st
from PIL import Image
import requests
import matplotlib.pyplot as plt

# Face++ API key and secret (replace with your actual key and secret)
API_KEY = 'cvu3BGKt2jDVN116fgj9HcT3qA7HcKJW'
API_SECRET = 'BBGSKpH54bMUB4HCZDjFWOY8yffdvgOp'

def image_to_byte_array(image: Image) -> bytes:
    """Convert image to byte array."""
    from io import BytesIO
    img_byte_array = BytesIO()
    image.save(img_byte_array, format='PNG')
    img_byte_array = img_byte_array.getvalue()
    return img_byte_array

# Function to detect faces and analyze the uploaded image using Face++
def analyze_face(image):
    img_byte_array = image_to_byte_array(image)
    url = "https://api-us.faceplusplus.com/facepp/v3/detect"
    
    files = {'image_file': img_byte_array}
    data = {
        'api_key': API_KEY,
        'api_secret': API_SECRET,
        'return_attributes': 'age,gender,emotion'
    }
    
    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing face: {e}")
        return {}

# Function to calculate ideal body weight range
def calculate_ideal_weight_range(height, gender):
    """Calculate ideal weight range (±10% of ideal weight)."""
    if gender.lower() == "male":
        ideal_weight = 50 + 0.9 * (height - 152.4)
    else:
        ideal_weight = 45.5 + 0.9 * (height - 152.4)

    lower_bound = ideal_weight * 0.9
    upper_bound = ideal_weight * 1.1
    return lower_bound, upper_bound

# Function to calculate BMR
def calculate_bmr(weight, height, age, gender):
    """Calculate BMR using the Mifflin-St Jeor Equation."""
    if gender.lower() == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

# Function to calculate calorie intake based on fitness goal

def calculate_calorie_intake(bmr, goal):
    """Adjust calorie intake based on user's fitness goal."""
    calorie_intake = bmr * 1.2  # Default multiplier for maintenance
    if goal == "Fat Loss":
        calorie_intake *= 0.8  # Reduce by 20%
    elif goal == "Muscle Gain":
        calorie_intake += 500  # Add 500 calories
    elif goal == "Body Recomposition":
        calorie_intake = bmr * 1.1  # Slight surplus
    elif goal == "Cutting Phase":
        calorie_intake *= 0.75  # Reduce by 25%

    # Ensure that calorie intake is always greater than 0 to avoid negative or zero values
    return max(calorie_intake, 1)  # Ensuring the calorie intake is at least 1 kcal


# Function to plot BMR vs Calorie Intake pie chart
def plot_bmr_vs_calorie_intake_pie(bmr, calorie_intake):
    """Plot a pie chart comparing BMR and suggested calorie intake."""
    remaining_calories = calorie_intake - bmr

    # Ensure values are non-negative
    bmr_value = max(bmr, 0)
    remaining_calories = max(remaining_calories, 0)

    # If both are 0, set them to 1 to avoid an empty pie chart
    if bmr_value == 0 and remaining_calories == 0:
        bmr_value = 1
        remaining_calories = 1

    # Categories and values for the pie chart
    categories = ['BMR', 'Remaining Calories']
    values = [bmr_value, remaining_calories]

    # Use smaller figure size for the pie chart
    fig, ax = plt.subplots(figsize=(4, 4))  # Smaller 4x4 inches pie chart
    ax.pie(
        values,
        labels=categories,
        autopct='%1.1f%%',
        startangle=90,
        colors=['#00BFFF', '#FF6347'],
        explode=(0.1, 0)
    )
    return fig




# Function to plot real-time pie chart for emotion analysis
def plot_emotion_pie_chart(emotions):
    """Plot a pie chart for emotion percentages."""
    labels = list(emotions.keys())
    values = list(emotions.values())
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
    ax.set_title("Real-Time Emotion Analysis")
    plt.axis('equal')  # Ensure pie is a circle
    return fig

# Streamlit UI
def app(): 
    """Main Streamlit app function."""
    st.set_page_config(page_title="Face Analysis with Fitness Goals", page_icon="🧑‍⚕️", layout="wide")

    # Sidebar UI elements
    st.title("Face Analysis with Fitness Goals")
    uploaded_file = st.sidebar.file_uploader("Upload Your Photo", type=["jpg", "png"])

    # Sidebar inputs for height, weight, age, and gender
    st.sidebar.header("User Information")
    weight = st.sidebar.number_input("Current Weight (kg)", min_value=30, max_value=300, value=70)
    height = st.sidebar.number_input("Height (cm)", min_value=100, max_value=250, value=170)
    age = st.sidebar.number_input("Age (years)", min_value=1, max_value=120, value=25)
    gender = st.sidebar.selectbox("Gender", options=["Male", "Female"])

    # Fitness goal selection
    goal = st.sidebar.selectbox("Fitness Goal", options=[
        "Fat Loss", "Muscle Gain", "Body Recomposition", "Cutting Phase", "Body Maintenance"
    ])

    # Calculate and display ideal weight range
    if height and gender:
        lower_ideal_weight, upper_ideal_weight = calculate_ideal_weight_range(height, gender)
        st.sidebar.subheader(f"Ideal Weight Range: {lower_ideal_weight:.2f} kg - {upper_ideal_weight:.2f} kg")

    # Check if weight, height, and age inputs are provided
    if weight and height and age and gender:
        # Calculate BMR
        bmr = calculate_bmr(weight, height, age, gender)

        # Adjust calorie intake based on goal
        calorie_intake = calculate_calorie_intake(bmr, goal)

        # Display BMR and calorie information
        if calorie_intake > 0:
            st.subheader(f"Your BMR: {bmr:.2f} kcal/day")
            st.subheader(f"Suggested Daily Calorie Intake for {goal}: {calorie_intake:.2f} kcal/day")

            # Visualization: Pie chart for BMR vs Calorie Intake
            fig_bmr = plot_bmr_vs_calorie_intake_pie(bmr, calorie_intake)
            st.pyplot(fig_bmr)
        else:
            st.error("Invalid calorie intake calculated. Please check your inputs.")

    # Check if the file is uploaded
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image = image.resize((400, 400))  # Resize the image to a manageable size
        st.sidebar.image(image, caption="Uploaded Image", use_container_width=True)

        # Analyze face using Face++ API if an image is uploaded
        if st.sidebar.button("Analyze Face"):
            response = analyze_face(image)
            
            # Check if the response contains faces and attributes
            if 'faces' in response and len(response['faces']) > 0:
                face = response['faces'][0]
                if 'attributes' in face:
                    # Display age and gender
                    st.write(f"Detected face is approximately {face['attributes']['age']['value']} years old.")
                    st.write(f"Gender: {face['attributes']['gender']['value']}")
        
                    # Display emotions
                    emotions = face['attributes']['emotion']
                    st.write("Emotion Analysis (in %):")
                    for emotion, value in emotions.items():
                        st.write(f"  - {emotion.capitalize()}: {value:.2f}%")

                    # Plot real-time pie chart for emotions
                    st.subheader("Emotion Analysis Pie Chart")
                    fig_emotions = plot_emotion_pie_chart(emotions)
                    st.pyplot(fig_emotions)
                else:
                    st.write("No attributes found for the detected face.")
            else:
                st.write("No face detected in the image.")
    else:
        st.write("Please upload an image to analyze.")

if __name__ == "__main__":
    app()
