import os
import sys

# Print Python and environment information
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")

try:
    import tensorflow as tf
    print(f"TensorFlow version: {tf.__version__}")
    print(f"TensorFlow path: {tf.__path__}")
    print("TensorFlow GPU available:", tf.config.list_physical_devices('GPU'))
    
    # Try to access keras layers
    from tensorflow.keras.layers import BatchNormalization
    print("Successfully imported BatchNormalization")
    
    # Test loading your model
    if os.path.exists("analysis/cnn/model.h5"):
        print("Model file exists!")
        
        # Define a custom BatchNormalization class
        class CustomBatchNormalization(tf.keras.layers.BatchNormalization):
            def __init__(self, **kwargs):
                if 'axis' in kwargs and isinstance(kwargs['axis'], list):
                    kwargs['axis'] = kwargs['axis'][0]
                super(CustomBatchNormalization, self).__init__(**kwargs)
            
            @classmethod
            def from_config(cls, config):
                if 'axis' in config and isinstance(config['axis'], list):
                    config['axis'] = config['axis'][0]
                return super(CustomBatchNormalization, cls).from_config(config)
        
        try:
            model = tf.keras.models.load_model(
                "analysis/cnn/model.h5",
                custom_objects={'BatchNormalization': CustomBatchNormalization},
                compile=False
            )
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
    else:
        print("Model file not found")
        
except ImportError as e:
    print(f"ImportError: {str(e)}")
    print("\nTrying alternative import paths...")
    
    try:
        import keras
        print(f"Standalone Keras version: {keras.__version__}")
        from keras.layers import BatchNormalization
        print("Successfully imported BatchNormalization from standalone Keras")
    except ImportError as e2:
        print(f"Keras ImportError: {str(e2)}")