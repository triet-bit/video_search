import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration

class BLIP2Reranker:
    def __init__(self, device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-opt-2.7b",
            torch_dtype=torch.float16  
        ).to(self.device).eval()
        self.yes_id = self.processor.tokenizer.encode("Yes", add_special_tokens=False)[0]
        self.no_id  = self.processor.tokenizer.encode("No",  add_special_tokens=False)[0]
                                                      
    def rerank(self, query: str, image_paths: list[str], top_k: int = 10) -> list[int]:
        return self.batch_rerank(query,image_paths,top_k)
    def batch_rerank(self, query: str, image_paths: list[str], top_k: int = 20, bs = 1) -> list[int]: 
        """
        rerank nhiều ảnh cùng lúc, dùng cho multi-chunk query. return list of ranked indices.
        """
        from concurrent.futures import ThreadPoolExecutor
        all_scores = []
        prompt = f"Question: Does this image show '{query}'? Answer:"
        def load_image(image_path): 
            return Image.open(image_path).comvert("RGB")
        for i in range(0, len(image_paths), bs): 
            batch_paths = image_paths[i:i+bs]
            with ThreadPoolExecutor() as executor: 
                images = list(executor.map(load_image,batch_paths))
            inputs = self.processor(
                images=images,
                text=[prompt] * len(images),
                return_tensors="pt",
                padding=True
            ).to(self.device, torch.float16)
            with torch.no_grad():
                with torch.cuda.amp.autocast():
                    outputs = self.model(**inputs)
            next_token_logits = outputs.logits[:, -1, :]
            yes_no_logits = next_token_logits[:, [self.yes_id, self.no_id]]  
            probs = torch.softmax(yes_no_logits, dim=-1)
            all_scores.extend(probs[:, 0].tolist())
        ranked = sorted(range(len(all_scores)), key=lambda i: all_scores[i], reverse=True)
        return ranked[:top_k]   