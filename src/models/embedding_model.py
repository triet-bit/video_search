import torch
import numpy as np
from PIL import Image
from transformers import AutoProcessor, AutoModel

class SiglipEncoder:
    def __init__(self, model_name: str = "google/siglip2-so400m-patch14-384", device: str = None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
            
        self.model_name = model_name
        
        print(f"Loading model {self.model_name} to {self.device}...")
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device).eval()
        self.processor = AutoProcessor.from_pretrained(self.model_name)

    def _extract_and_normalize(self, outputs) -> np.ndarray:
        if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
            feat = outputs.pooler_output  # (1, dim)
        else:
            feat = outputs.last_hidden_state[:, 0, :]  # CLS token
        
        feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat[0].cpu().numpy().astype(np.float32)

    def encode_text(self, text: str, max_length: int = 64) -> np.ndarray:
        inputs = self.processor(
            text=[text], 
            return_tensors="pt", 
            padding="max_length", 
            max_length=max_length
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.get_text_features(**inputs)
            
        return self._extract_and_normalize(outputs)

    def encode_image(self, image_path: str) -> np.ndarray:
        """
        Mã hóa hình ảnh thành vector đặc trưng.
        """
        img = Image.open(image_path).convert("RGB")
        inputs = self.processor(
            images=img, 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.get_image_features(**inputs)
            
        return self._extract_and_normalize(outputs)
    