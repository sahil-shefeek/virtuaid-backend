import os
import json
import h5py
import numpy as np
import tensorflow as tf

class CustomBatchNormalization(tf.keras.layers.BatchNormalization):
    def __init__(self, axis=3, **kwargs):
        # Handle list axis parameter
        if isinstance(axis, list):
            axis = axis[0]  # Take first element if it's a list
        super().__init__(axis=axis, **kwargs)
    
    @classmethod
    def from_config(cls, config):
        # Fix axis parameter in config
        if 'axis' in config and isinstance(config['axis'], list):
            config['axis'] = config['axis'][0]
        return super(CustomBatchNormalization, cls).from_config(config)

def load_model_with_fixes(model_path):
    """Try multiple approaches to load the model"""
    print(f"Attempting to load model from: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        return None
        
    # Approach 1: Use custom objects with clear registration
    try:
        print("Trying approach 1: Custom objects with explicit registration")
        with tf.keras.utils.custom_object_scope({'BatchNormalization': CustomBatchNormalization}):
            model = tf.keras.models.load_model(model_path, compile=False)
            print("Model loaded successfully with approach 1!")
            return model
    except Exception as e:
        print(f"Approach 1 failed: {str(e)}")
    
    # Approach 2: Load and modify model structure manually
    try:
        print("Trying approach 2: Manual model structure modification")
        # Open the H5 file
        with h5py.File(model_path, 'r') as h5file:
            # Check if it contains model_config
            if 'model_config' in h5file.attrs:
                model_config = json.loads(h5file.attrs['model_config'].decode('utf-8'))
                
                # Modify BatchNormalization layers in the config
                def fix_batch_norm_config(config):
                    if isinstance(config, dict):
                        if config.get('class_name') == 'BatchNormalization' and 'config' in config:
                            if 'axis' in config['config'] and isinstance(config['config']['axis'], list):
                                config['config']['axis'] = config['config']['axis'][0]
                        
                        # Process nested dictionaries
                        for key, value in config.items():
                            if isinstance(value, (dict, list)):
                                config[key] = fix_batch_norm_config(value)
                    
                    elif isinstance(config, list):
                        # Process lists
                        for i, item in enumerate(config):
                            if isinstance(item, (dict, list)):
                                config[i] = fix_batch_norm_config(item)
                    
                    return config
                
                # Apply fixes to the model config
                fixed_config = fix_batch_norm_config(model_config)
                
                # Create model from fixed config
                fixed_model = tf.keras.models.model_from_json(json.dumps(fixed_config))
                
                # Load weights
                fixed_model.load_weights(model_path)
                print("Model loaded successfully with approach 2!")
                return fixed_model
    except Exception as e:
        print(f"Approach 2 failed: {str(e)}")
    
    # Approach 3: Use SavedModel format as intermediate step
    try:
        print("Trying approach 3: Convert through SavedModel format")
        # Create a temporary directory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_saved_model = os.path.join(temp_dir, "temp_model")
            
            # Use low-level TF ops to load and save the model
            with tf.keras.utils.custom_object_scope({'BatchNormalization': CustomBatchNormalization}):
                try:
                    # First attempt to load with custom objects
                    model = tf.keras.models.load_model(model_path, compile=False)
                except:
                    # If that fails, try loading as a generic model without custom layers
                    model = tf.keras.models.load_model(
                        model_path,
                        custom_objects={'BatchNormalization': tf.keras.layers.BatchNormalization},
                        compile=False
                    )
                
                # Save as SavedModel format
                model.save(temp_saved_model, save_format='tf')
                
                # Reload from SavedModel format
                reloaded_model = tf.keras.models.load_model(temp_saved_model)
                print("Model loaded successfully with approach 3!")
                return reloaded_model
    except Exception as e:
        print(f"Approach 3 failed: {str(e)}")
        
    print("All approaches failed to load the model.")
    return None

# Test the function
if __name__ == "__main__":
    model_path = "analysis/cnn/model.h5"
    model = load_model_with_fixes(model_path)
    
    if model:
        print("Model loaded successfully!")
        model.summary()
    else:
        print("Failed to load model.")