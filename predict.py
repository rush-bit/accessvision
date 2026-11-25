
from ultralytics import YOLO

# Load trained WalkSentry model
model = YOLO("weights/best.pt")

# Display available classes
print("Detected classes:", model.names)

# Run prediction
results = model.predict(
    source="test_image.jpg",
    conf=0.25,
    save=True,
    show=True
)

print("Prediction completed!")
