import sys
print("Starting import...")
try:
    import tensorflow as tf
    print(f"TensorFlow Version: {tf.__version__}")
    print("Import Success!")
except Exception as e:
    print(f"Import Failed: {e}")
