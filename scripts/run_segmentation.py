import cv2

from detectors.yolov8_detector import YOLOv8Detector

MODEL_PATH = "yolov8n-seg.pt"
IMAGE_PATH = "path/to/your/image.jpg"

detector = YOLOv8Detector(MODEL_PATH, task="segment")
image = cv2.imread(IMAGE_PATH)
results = detector.predict(image)

for i, det in enumerate(results):
    mask = det["mask"]
    mask_img = (mask * 255).astype("uint8")
    color_mask = cv2.applyColorMap(mask_img, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(image, 0.7, color_mask, 0.3, 0)
    cv2.imshow(f"Mask {i}", overlay)
    cv2.imwrite(f"segmented_{i}.jpg", overlay)

cv2.waitKey(0)
cv2.destroyAllWindows()
