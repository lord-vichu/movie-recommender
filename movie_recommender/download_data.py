import fiftyone as fo
import fiftyone.zoo as foz

# 1. Select the classes you want. 
# Note: Open Images has 'Ambulance' but NOT 'Fire Truck' as a main class.
# We download 'Truck' and you will filter for Fire Trucks later.
classes = ["Ambulance", "Truck", "Car", "Van"]

# 2. Download the dataset
# This searches the database and downloads only the relevant images.
dataset = foz.load_zoo_dataset(
    "open-images-v7",
    split="train",                  # 'train', 'validation', or 'test'
    label_types=["detections"],     # We only want bounding boxes
    classes=classes,
    max_samples=2000,               # Limit to 2000 images to save space/time
    shuffle=True,                   # Randomize so you get a good mix
    seed=42
)

# 3. Export to YOLO format (Ready for training)
export_dir = "./emergency_vehicle_dataset"
dataset.export(
    export_dir=export_dir,
    dataset_type=fo.types.YOLOv5Dataset,  # Works for YOLOv8/v11 too
    label_field="ground_truth",
)

print(f"Dataset downloaded to {export_dir}")