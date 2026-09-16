# ai-memory-bridge

RAG (Retrieval-Augmented Generation) system để truy vấn lịch sử trò chuyện (chat history) bằng ngôn ngữ tự nhiên. Dự án được xây dựng như bước thứ 3 trong portfolio cá nhân, tiếp nối kiến trúc provider abstraction đã áp dụng ở `financial-transaction-analyzer` và `ai-transaction-classifier`.

## Vấn đề giải quyết

Sau nhiều buổi học/làm việc với AI assistant, lượng ghi chú và hội thoại tích lũy rất lớn, khó tìm lại thông tin cũ bằng cách đọc lại từng file. `ai-memory-bridge` cho phép hỏi bằng câu hỏi tự nhiên ("Tôi đã học gì về SQL?") và hệ thống tự tìm đoạn hội thoại liên quan nhất, rồi dùng LLM tổng hợp câu trả lời dựa trên đúng nội dung tìm được — không bịa thông tin ngoài phạm vi dữ liệu đã cung cấp.

## Kiến trúc

```
sample_data.json (hoặc conversations.json thật)
        |
        v
   ingest.py  --chunking (window + overlap)--> chunks
        |
        v
  PrefixProvider.generate_prefix()  --> gắn prefix tóm tắt chủ đề cho từng chunk
        |
        v
   ChromaDB (persistent, lưu tại ./chroma_db)
        |
        v
   query.py --> search() tìm top-k chunk gần nhất với câu hỏi
        |
        v
  AnswerProvider.generate_answer() --> LLM tổng hợp câu trả lời từ context tìm được
```

Cả `PrefixProvider` và `AnswerProvider` đều là abstract base class, có 3 implementation:
- `MockProvider` / `MockAnswerProvider`: không gọi API, dùng để test luồng code miễn phí
- `GeminiProvider`: dùng Gemini API (free tier) cho cả 2 tác vụ
- `AnthropicProvider`: dùng Claude API (mới implement cho prefix, chưa test thật)

Kiến trúc này cho phép đổi qua lại giữa provider mà không sửa code gọi hàm — chỉ đổi dòng khởi tạo instance.

## Các quyết định kỹ thuật và bài học thực nghiệm

### 1. Chunk size và vấn đề "trộn chủ đề"
Chunk quá lớn (ví dụ 4 message/chunk) dễ bị trộn nhiều chủ đề khác nhau trong cùng 1 vector, khiến embedding bị "mờ nhòe" và làm giảm độ chính xác retrieval — ngay cả khi chunk đó chứa câu trả lời đúng nhất. Giảm chunk_size xuống 2 (kèm overlap 1) giải quyết được vấn đề này rõ rệt trong thử nghiệm thực tế: chunk chứa câu trả lời đúng về SQL nhảy từ hạng 3 (khoảng cách 1.31) lên hạng 1 (khoảng cách 1.00).

### 2. Giới hạn của contextual prefix
Ban đầu kỳ vọng dùng LLM sinh prefix tóm tắt chủ đề cho từng chunk sẽ cải thiện retrieval. Thực nghiệm cho thấy điều ngược lại trong trường hợp chunk bị trộn chủ đề: prefix "trung thực" của Gemini (ví dụ "Thảo luận về SQL và phát hiện outlier") lại khiến vector bị kéo xa hơn khỏi câu hỏi chỉ hỏi về 1 chủ đề, vì nó phản ánh đúng thực tế là chunk có 2 nội dung khác nhau. Kết luận: **contextual prefix chỉ nên dùng để bù đắp ngữ cảnh nền bị thiếu, không phải để sửa lỗi cấu trúc chunking**. Vấn đề trộn chủ đề cần được giải quyết ở bước chunking, không phải ở bước prefix.

### 3. Câu hỏi chung chung khó match chunk chứa thuật ngữ kỹ thuật cụ thể
Với câu hỏi chung chung ("Homos học gì về SQL?"), chunk chỉ chứa câu hỏi (không có câu trả lời) đôi khi xếp hạng cao hơn chunk chứa câu trả lời đầy đủ và cụ thể (ví dụ liệt kê ROW_NUMBER, RANK, SUM OVER) — vì vector của chunk chi tiết bị "đẩy xa" khỏi vector câu hỏi chung chung do chứa nhiều thuật ngữ mà câu hỏi không nhắc tới. Đây là 1 giới hạn cố hữu của retrieval dựa trên embedding similarity thuần túy; hệ thống production thường giải quyết bằng re-ranking (chưa implement trong bản này).

### 4. Xử lý lỗi API thực tế
Trong quá trình phát triển đã gặp cả 3 loại lỗi từ Gemini free tier: `503 UNAVAILABLE` (server quá tải), `429` per-minute rate limit (5 request/phút), và `429` per-day quota (20 request/ngày). Đã thêm try/except quanh mọi lời gọi API — khi lỗi xảy ra, chương trình in thông báo rõ ràng và tiếp tục chạy (bỏ qua chunk/câu hỏi lỗi) thay vì crash toàn bộ.

## Cách chạy

```bash
pip install chromadb google-genai anthropic

# Set biến môi trường (chọn 1 hoặc cả 2)
setx GOOGLE_API_KEY "your-key"
setx ANTHROPIC_API_KEY "your-key"

python ingest.py
python query.py "câu hỏi của bạn"
```

Mặc định dùng `MockProvider`/`MockAnswerProvider` để test không tốn API call — đổi provider trong `if __name__ == "__main__":` của từng file để dùng Gemini/Anthropic thật.

## Hạn chế hiện tại

- Dữ liệu mẫu (`sample_data.json`) là dữ liệu giả lập, chưa tích hợp với export thật từ Claude.ai
- Chunking dùng fixed window + overlap, chưa có semantic chunking (chia theo ranh giới ý)
- Chưa có re-ranking sau bước vector search
- `AnthropicProvider` cho `AnswerProvider` chưa được viết/test
- ChromaDB chạy local persistent, chưa tính đến scale cho dữ liệu lớn

## Hướng phát triển tiếp theo

- Tích hợp dữ liệu thật từ Claude.ai export (`conversations.json`)
- Thử nghiệm semantic chunking thay cho fixed window
- Thêm re-ranking layer
- Áp dụng lại kiến trúc RAG này cho `ai-transaction-classifier`
