from google import genai
import time
import json
from dotenv import load_dotenv
import os
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = 'gemini-2.5-flash'

def get_client():
    return genai.Client(api_key=GOOGLE_API_KEY)
def evaluate_batch_with_gemini(batch_data):
    client = get_client()
    prompt = """Bạn là giám khảo chấm điểm hệ thống trích xuất thông tin Factual.
Nhiệm vụ: So sánh [Đáp án chuẩn] và [Dự đoán]. Chúng có mang cùng một lượng thông tin sự thật trong ngữ cảnh câu trả lời ngắn không? (Bỏ qua khác biệt về viết tắt, thứ tự danh sách, hay định dạng số).
Trả về MỘT MẢNG JSON duy nhất chứa các số 1 (Đúng/Tương đương) hoặc 0 (Sai/Không tương đương). 
Ví dụ kết quả mong muốn: [1, 0, 1, 1, 0]
 
Danh sách các cặp cần đánh giá:
"""
    for i, item in enumerate(batch_data): 
        prompt += f"{i+1}. [Đáp án chuẩn]: {item['gt']} | [Dự đoán]: {item['pred']}\n"
    retries = 1 
    for _ in range(retries): 
        try:
            response = client.models.generate_content(
                model= MODEL_NAME, 
                contents = prompt, 
                config = {
                    "response_mime_type":"application/json"
                } 
            )
            return_lst = [int(x.strip()) for x in response.text.replace("[","").replace("]","").split(",")]

            return return_lst
        except Exception as e: 
            print("error in evaluate llm score",e)
    return []




hard_cases = [
    {"gt": "eu, nga", "pred": "Nga, Liên minh châu Âu"},
    {"gt": "10m bia di động nam; 330,5", "pred": "811,5"},
    {"gt": "Zara Tindall 1981", "pred": "zara tindall (1981)"},
    {"gt": "25/9/2023", "pred": "ngày 25 tháng 9 năm 2023"},
    {"gt": "cơ quan nhà nước, cán bộ, công chức, viên chức, người lao động trong cơ quan nhà nước sử dụng mxh, tổ chức, cá nhân khác sử dụng mxh, nhà cung cấp dịch vụ mxh tại việt nam", "pred": "cơ quan nhà nước, cán bộ, công chức, viên chức, người lao động trong cơ quan nhà nước sử dụng mxh; tổ"},
    {"gt": "chủ động khai báo về tình trạng sức khỏe bất thường", "pred": "chủ động khai báo về tình trạng sức khỏe bất thường với tổ chức kiểm dịch y tế biên giới nơi nhập cảnh, xuất cảnh, quá cảnh"},
]
print(evaluate_batch_with_gemini(hard_cases))


