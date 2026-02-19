import torch
import torch.nn as nn
import timm
import numpy as np
import cv2
from PIL import Image
from skimage.measure import shannon_entropy
import piexif
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from torchvision import transforms
import gc

# ----------------------------
# 1. Device Setup
# ----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ----------------------------
# 2. Load EfficientNet Model
# ----------------------------
model = timm.create_model('efficientnet_b0', pretrained=True)
model.classifier = nn.Linear(model.classifier.in_features, 2)

model.load_state_dict(
    torch.load("best_model.pth",
               map_location=device,
               weights_only=True)
)

model.to(device)
model.eval()

class_names = ["FAKE", "REAL"]

# ----------------------------
# 3. Image Transform
# ----------------------------
# MUST MATCH validation transform used during training
validation_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ----------------------------
# 4. Metadata Analysis
# ----------------------------
def advanced_metadata_analysis(image_path):

    score = 0.0
    metadata_results = {}

    suspicious_keywords = [
        "stable", "midjourney", "dall", "ai",
        "photoshop", "adobe", "gimp",
        "generated", "synthetic"
    ]

    # EXIF analysis
    try:
        exif_dict = piexif.load(image_path)

        if exif_dict["0th"]:
            metadata_results["has_exif"] = True

            software_tag = exif_dict["0th"].get(
                piexif.ImageIFD.Software
            )

            if software_tag:
                software = software_tag.decode(
                    errors="ignore"
                ).lower()

                metadata_results["software"] = software

                if any(word in software for word in suspicious_keywords):
                    score += 0.5
        else:
            metadata_results["has_exif"] = False
            score += 0.1

    except:
        metadata_results["has_exif"] = False
        score += 0.1

    # Hachoir metadata
    try:
        parser = createParser(image_path)

        if parser:
            metadata = extractMetadata(parser)

            if metadata:
                meta_text = str(metadata).lower()
                metadata_results["hachoir"] = meta_text[:300]

                if any(word in meta_text for word in suspicious_keywords):
                    score += 0.4

    except:
        pass

    # Binary scan
    try:
        with open(image_path, "rb") as f:
            raw = f.read().lower()

            if b"whatsapp" in raw:
                metadata_results["whatsapp"] = True
                score += 0.2

            if b"stable" in raw:
                score += 0.4

    except:
        pass

    return min(score, 1.0), metadata_results


# ----------------------------
# 5. Entropy Analysis (FIXED)
# ----------------------------
def entropy_analysis(image_path):

    with Image.open(image_path) as img:
        img = img.convert("L")
        img_np = np.array(img)

    entropy = shannon_entropy(img_np)

    score = 0.2 if entropy < 4.5 else 0.0

    return score, entropy


# ----------------------------
# 6. Noise Analysis (FIXED)
# ----------------------------
def noise_analysis(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return 0.0, 0.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    variance = cv2.Laplacian(gray, cv2.CV_64F).var()

    # RELEASE MEMORY
    del img
    del gray
    gc.collect()

    score = 0.2 if variance < 50 else 0.0

    return score, variance


# ----------------------------
# 7. Resolution Analysis (FIXED)
# ----------------------------
def resolution_analysis(image_path):

    with Image.open(image_path) as img:
        width, height = img.size

    score = 0.2 if (width, height) in [
        (512,512),
        (768,768),
        (1024,1024)
    ] else 0.0

    return score, (width, height)


# ----------------------------
# 8. Model Prediction (FIXED)
# ----------------------------
def model_prediction(image_path):

    image = Image.open(image_path).convert("RGB")

    image = validation_transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.softmax(outputs, dim=1)

    fake_prob = probabilities[0][0].item()
    real_prob = probabilities[0][1].item()

    return fake_prob, real_prob



# ----------------------------
# 9. Final Decision Engine (IMPROVED)
# ----------------------------
def decision_engine(image_path):

    fake_prob, real_prob = model_prediction(image_path)

    meta_score, meta_details = advanced_metadata_analysis(image_path)

    entropy_score, entropy = entropy_analysis(image_path)

    noise_score, variance = noise_analysis(image_path)

    res_score, resolution = resolution_analysis(image_path)

    forensic_score = (
        0.4 * entropy_score +
        0.4 * noise_score +
        0.2 * res_score
    )

    # FINAL WEIGHTED FUSION
    final_score = (
        0.85 * fake_prob +
        0.10 * meta_score +
        0.05 * forensic_score
    )

    # DECISION THRESHOLD
    if final_score > 0.75:
        decision = "AI-GENERATED"
    else:
        decision = "REAL"

    confidence = round(
        max(final_score, 1 - final_score) * 100,
        2
    )

    # DEBUG LOG
    print("\n----- AI Image Detection Result -----")
    print("Fake Probability:", round(fake_prob,4))
    print("Metadata Score:", round(meta_score,4))
    print("Forensic Score:", round(forensic_score,4))
    print("Final Score:", round(final_score,4))
    print("Decision:", decision)
    print("-------------------------------------")

    return decision, confidence
