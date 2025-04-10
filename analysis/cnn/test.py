import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import BatchNormalization

# Enhanced CustomBatchNormalization to handle all serialization issues
class CustomBatchNormalization(BatchNormalization):
    def __init__(self, **kwargs):
        # Handle axis parameter format differences
        if 'axis' in kwargs:
            if isinstance(kwargs['axis'], list):
                kwargs['axis'] = kwargs['axis'][0]
        super(CustomBatchNormalization, self).__init__(**kwargs)
        
    # Add custom from_config and get_config methods
    @classmethod
    def from_config(cls, config):
        # Ensure axis is an integer
        if 'axis' in config and isinstance(config['axis'], list):
            config['axis'] = config['axis'][0]
        return super(CustomBatchNormalization, cls).from_config(config)

def predict_emotion(image_path, model):
    # Update emotion labels to match the three-emotion model
    emotion_labels = ["angry", "sad", "happy"]
    
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (48, 48)) / 255.0
    img = img.reshape(1, 48, 48, 1)

    prediction = model.predict(img)
    emotion = emotion_labels[np.argmax(prediction)]
    confidence = np.max(prediction)
    
    return emotion, confidence

def test_emotion_detection(model_path, image_path=None, use_webcam=False):
    # Update emotion labels to match the three-emotion model
    emotion_labels = ["angry", "sad", "happy"]
    
    try:
        # Load model with custom BatchNormalization implementation
        print(f"Loading model from {model_path}...")
        model = load_model(
            model_path, 
            custom_objects={'BatchNormalization': CustomBatchNormalization},
            compile=False
        )
        model.compile(
            # Update optimizer to match training parameters
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        print("Model loaded successfully")
        
        if use_webcam:
            # Process webcam feed
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open webcam")
                return
                
            print("Press 'q' to exit")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Process frame (convert to grayscale and resize)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, (48, 48)) / 255.0
                img_array = resized.reshape(1, 48, 48, 1)
                
                # Get predictions
                predictions = model.predict(img_array, verbose=0)
                
                # Display results on frame
                max_index = np.argmax(predictions[0])
                max_emotion = emotion_labels[max_index]
                max_prob = np.max(predictions[0])
                
                cv2.putText(frame, f"{max_emotion}: {max_prob:.2f}", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Show frame
                cv2.imshow('Emotion Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            cap.release()
            cv2.destroyAllWindows()
            
        elif image_path:
            # Process single image
            if not os.path.exists(image_path):
                print(f"Error: Image file not found at {image_path}")
                return
                
            emotion, confidence = predict_emotion(image_path, model)
            print(f"Predicted Emotion: {emotion} (Confidence: {confidence:.4f})")
                
            # Display image with prediction
            img = cv2.imread(image_path)
            cv2.putText(img, f"{emotion}: {confidence:.2f}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow('Emotion Detection', img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Update path to the new three-emotion model
    model_path = "analysis/cnn/three_emotion_model.h5"
    
    # Choose one of the following options:
    # 1. Test with a single image
    test_emotion_detection(model_path, image_path="analysis/cnn/test_images/sad_test.jpg")
    
    # 2. Test with webcam
    # test_emotion_detection(model_path, use_webcam=True)