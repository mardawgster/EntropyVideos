from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from scipy.stats import entropy
import tempfile
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_shannon(hist):
    return entropy(hist, base=2)

def calculate_renyi(hist, alpha):
    if alpha == 1: return calculate_shannon(hist)
    return (1 / (1 - alpha)) * np.log2(np.sum(hist**alpha) + 1e-10)

def calculate_tsallis(hist, q):
    if q == 1: return calculate_shannon(hist)
    return (1 / (q - 1)) * (1 - np.sum(hist**q))

@app.post("/analyze-entropy")
async def analyze_entropy(
    file: UploadFile = File(...),
    n_frame: int = Form(10),
    alpha: float = Form(2.0),
    q: float = Form(2.0),
    roi: str = Form("[0, 0, 500, 500]"),
    calc_shannon: str = Form("true"),
    calc_renyi: str = Form("true"),
    calc_tsallis: str = Form("true")
):
    mask_params = json.loads(roi)
    
    # Convert string booleans from JS FormData
    do_shannon = calc_shannon.lower() == "true"
    do_renyi = calc_renyi.lower() == "true"
    do_tsallis = calc_tsallis.lower() == "true"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(await file.read())
        video_path = tmp.name

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    data = []
    frame_idx = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
                
            if frame_idx % n_frame == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                x, y, w, h = mask_params
                
                h_img, w_img = gray.shape
                roi_img = gray[max(0, y):min(h_img, y+h), max(0, x):min(w_img, x+w)]
                
                if roi_img.size > 0:
                    hist = cv2.calcHist([roi_img], [0], None, [256], [0, 256]).flatten()
                    hist = hist / (hist.sum() + 1e-10)
                    
                    # Only calculate what the user requested
                    frame_data = {"time": frame_idx / fps}
                    if do_shannon: frame_data["shannon"] = float(calculate_shannon(hist))
                    if do_renyi: frame_data["renyi"] = float(calculate_renyi(hist, alpha))
                    if do_tsallis: frame_data["tsallis"] = float(calculate_tsallis(hist, q))
                    
                    data.append(frame_data)
            frame_idx += 1
    finally:
        cap.release()
        os.remove(video_path)
        
    return {"data": data, "fps": fps}