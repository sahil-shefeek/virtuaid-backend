import os
import cv2
import tempfile
import numpy as np
from PIL import Image
import tensorflow as tf
from django.conf import settings
from typing import Dict, List, Tuple

class EmotionDetector:
    """Class to handle emotion detection in video frames"""
    
    def __init__(self, model_path=None):
        """Initialize the emotion detector with a model path"""
        if model_path is None:
            # Default model path updated to new three-emotion model
            self.model_path = os.path.join(settings.BASE_DIR, 'analysis/cnn/three_emotion_model.h5')
        else:
            self.model_path = model_path
        
        self.model = None
        # Updated emotions list to match new model
        self.emotions = ['angry', 'sad', 'happy']
        # Updated image size to 48x48 to match new model
        self.img_size = (48, 48)
    
    def load_model(self):
        """Load the TensorFlow model"""
        if self.model is None:
            try:
                # Define custom BatchNormalization class
                class CustomBatchNormalization(tf.keras.layers.BatchNormalization):
                    def __init__(self, **kwargs):
                        if 'axis' in kwargs and isinstance(kwargs['axis'], list):
                            kwargs['axis'] = kwargs['axis'][0]
                        super(CustomBatchNormalization, self).__init__(**kwargs)
                
                # Load model with custom objects
                self.model = tf.keras.models.load_model(
                    self.model_path, 
                    custom_objects={'BatchNormalization': CustomBatchNormalization},
                    compile=False
                )
                self.model.compile(
                    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
                    loss='categorical_crossentropy',
                    metrics=['accuracy']
                )
                print(f"Model loaded successfully from {self.model_path}")
                return True
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                return False
        return True
    
    def process_frame(self, frame) -> Dict[str, float]:
        """Process a single frame and return emotion predictions"""
        if not self.load_model():
            return None
        
        # Resize and preprocess the frame according to new model requirements
        try:
            # Convert to grayscale and resize to 48x48
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            img = cv2.resize(img, self.img_size)
            
            # Normalize pixel values (0-255 to 0-1)
            img = img / 255.0
            
            # Reshape for model input (add batch dimension and channel dimension)
            img_array = np.expand_dims(img, axis=0)  # Add batch dimension
            img_array = np.expand_dims(img_array, axis=-1)  # Add channel dimension
            
            # Get predictions
            predictions = self.model.predict(img_array, verbose=0)
            
            # Create dictionary of emotion probabilities
            results = {}
            for i, emotion in enumerate(self.emotions):
                results[emotion] = float(predictions[0][i])
                
            return results
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return None
    
    def extract_frames(self, video_path: str, frame_rate: float = 1.0) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames from a video file at a specified frame rate
        Returns list of tuples: (frame, timestamp)
        """
        frames = []
        
        try:
            # Open video file
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                print(f"Error: Could not open video file {video_path}")
                return frames
            
            # Get video properties
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            # Calculate frame interval based on desired frame_rate
            frame_interval = int(fps / frame_rate)
            if frame_interval < 1:
                frame_interval = 1
                
            print(f"Video FPS: {fps}, Duration: {duration}s, Frame interval: {frame_interval}")
            
            # Extract frames at the specified interval
            current_frame = 0
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                
                if current_frame % frame_interval == 0:
                    timestamp = current_frame / fps
                    frames.append((frame, timestamp))
                    
                current_frame += 1
                
            video.release()
            print(f"Extracted {len(frames)} frames from video")
            return frames
            
        except Exception as e:
            print(f"Error extracting frames: {str(e)}")
            return frames
    
    def analyze_video(self, video_path: str, frame_rate: float = 1.0) -> List[Dict]:
        """
        Analyze a video file and return emotion data for each frame
        Args:
            video_path: Path to the video file
            frame_rate: Number of frames per second to analyze
        Returns:
            List of dictionaries with timestamp and emotion data
        """
        results = []
        
        # Extract frames from the video
        frames = self.extract_frames(video_path, frame_rate)
        
        # Process each frame
        for frame, timestamp in frames:
            emotion_data = self.process_frame(frame)
            if emotion_data:
                result = {
                    'timestamp': timestamp,
                    **emotion_data
                }
                results.append(result)
        
        return results