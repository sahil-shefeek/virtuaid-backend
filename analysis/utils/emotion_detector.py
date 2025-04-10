import os
import cv2
import tempfile
import numpy as np
from PIL import Image
import tensorflow as tf
from django.conf import settings
from typing import Dict, List, Tuple, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

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
        logger.info(f"EmotionDetector initialized with model path: {self.model_path}")
    
    def load_model(self) -> bool:
        """
        Load the TensorFlow model
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        if self.model is None:
            try:
                logger.info(f"Loading model from {self.model_path}")
                
                # Check if model file exists
                if not os.path.exists(self.model_path):
                    logger.error(f"Model file not found at {self.model_path}")
                    return False
                
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
                logger.info(f"Model loaded successfully from {self.model_path}")
                return True
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}", exc_info=True)
                return False
        return True
    
    def process_frame(self, frame) -> Optional[Dict[str, float]]:
        """
        Process a single frame and return emotion predictions
        
        Args:
            frame: Input image frame as numpy array
            
        Returns:
            Dictionary with emotion probabilities or None if processing failed
        """
        if not self.load_model():
            logger.error("Failed to load model for frame processing")
            return None
        
        # Resize and preprocess the frame according to new model requirements
        try:
            # Check if frame is valid
            if frame is None or not isinstance(frame, np.ndarray):
                logger.error(f"Invalid frame type: {type(frame)}")
                return None
                
            # Convert to grayscale and resize to 48x48
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                img = frame  # Assume it's already grayscale
                
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
            
            # Log the highest emotion for debugging
            max_emotion = max(results, key=results.get)
            logger.debug(f"Frame analyzed - dominant emotion: {max_emotion} ({results[max_emotion]:.4f})")
                
            return results
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}", exc_info=True)
            return None
    
    def extract_frames(self, video_path: str, frame_rate: float = 1.0) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames from a video file at a specified frame rate
        
        Args:
            video_path: Path to the video file
            frame_rate: Number of frames per second to extract
            
        Returns:
            List of tuples: (frame, timestamp)
        """
        frames = []
        
        try:
            # Check if file exists and is readable
            if not os.path.exists(video_path):
                logger.error(f"Video file does not exist: {video_path}")
                return frames
                
            # Open video file
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                logger.error(f"Error: Could not open video file {video_path}")
                return frames
            
            # Get video properties
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            if fps <= 0 or frame_count <= 0:
                logger.error(f"Invalid video properties: fps={fps}, frame_count={frame_count}")
                video.release()
                return frames
            
            # Calculate frame interval based on desired frame_rate
            frame_interval = max(1, int(fps / frame_rate))
                
            logger.info(f"Video properties - FPS: {fps:.2f}, Duration: {duration:.2f}s, "
                       f"Frame count: {frame_count}, Frame interval: {frame_interval}")
            
            # Extract frames at the specified interval
            current_frame = 0
            frames_read = 0
            frames_extracted = 0
            
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                
                frames_read += 1
                if current_frame % frame_interval == 0:
                    timestamp = current_frame / fps
                    frames.append((frame.copy(), timestamp))
                    frames_extracted += 1
                    
                current_frame += 1
                
            video.release()
            
            # Validate extraction
            if frames_extracted == 0:
                logger.warning(f"No frames extracted from video (read {frames_read} frames)")
            else:
                logger.info(f"Extracted {frames_extracted} frames from video (read {frames_read} frames)")
                
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}", exc_info=True)
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
        
        try:
            # Extract frames from the video
            logger.info(f"Starting frame extraction for {video_path} at {frame_rate} fps")
            frames = self.extract_frames(video_path, frame_rate)
            
            if not frames:
                logger.error("No frames extracted from video")
                return results
                
            # Process each frame
            logger.info(f"Processing {len(frames)} frames for emotion detection")
            processed_count = 0
            failed_count = 0
            
            for frame, timestamp in frames:
                emotion_data = self.process_frame(frame)
                if emotion_data:
                    result = {
                        'timestamp': timestamp,
                        **emotion_data
                    }
                    results.append(result)
                    processed_count += 1
                else:
                    failed_count += 1
            
            success_rate = processed_count / len(frames) if frames else 0
            logger.info(f"Video analysis completed - Processed: {processed_count}, "
                       f"Failed: {failed_count}, Success rate: {success_rate:.2%}")
            
            if failed_count > 0:
                logger.warning(f"Some frames ({failed_count}) could not be processed")
            
            # Sort results by timestamp
            results.sort(key=lambda x: x['timestamp'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}", exc_info=True)
            return results