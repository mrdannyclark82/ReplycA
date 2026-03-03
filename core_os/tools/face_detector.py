import cv2
import os
import sys

def detect_faces(image_path):
    if not os.path.exists(image_path):
        return f"Error: Image {image_path} not found."

    # Load the Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        return "Error: Could not read image."

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    num_faces = len(faces)
    
    if num_faces > 0:
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # Save result
        output_path = image_path.replace(".jpg", "_detected.jpg")
        cv2.imwrite(output_path, img)
        return f"SUCCESS: Detected {num_faces} face(s). Result saved to {output_path}."
    else:
        return "NO_FACES: No faces detected in the image."

if __name__ == "__main__":
    path = "./core_os/screenshots/face_scan.jpg"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    print(detect_faces(path))
