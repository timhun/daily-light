import asyncio
import os
import sys
import edge_tts

VOICE = "zh-TW-YunJheNeural"

async def generate_speech(text_file_path, output_mp3_path):
    """
    讀取文字檔並生成語音。
    """
    try:
        with open(text_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"錯誤：文字檔 {text_file_path} 不存在。")
        return

    if not text.strip() or text.strip() in ["今日無內容", "今日晨間無內容", "今日晚間無內容"]:
        print(f"文字檔 {text_file_path} 內容為空或無需生成語音，跳過。")
        return
        
    print(f"正在為 {text_file_path} 生成語音...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_mp3_path)
    print(f"語音檔案已儲存至 {output_mp3_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python text_to_speech_edge.py <input_text_file> <output_mp3_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 確保輸出目錄存在
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    asyncio.run(generate_speech(input_file, output_file))
