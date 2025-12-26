"""
翻译模块 - 使用免费的翻译API
"""

from deep_translator import GoogleTranslator
import time
import re


class Translator:
    def __init__(self):
        self.translator = GoogleTranslator(source='en', target='zh-CN')
    
    def translate(self, text: str) -> str:
        """翻译文本到中文"""
        if not text or not text.strip():
            return ""
        
        try:
            # 清理HTML标签
            clean_text = re.sub(r'<[^>]+>', '', text)
            clean_text = clean_text.strip()
            
            if not clean_text:
                return ""
            
            # deep-translator有字符限制，需要分段翻译
            if len(clean_text) > 4500:
                chunks = self._split_text(clean_text, 4500)
                translated_chunks = []
                for chunk in chunks:
                    translated = self.translator.translate(chunk)
                    translated_chunks.append(translated)
                    time.sleep(0.5)  # 避免请求过快
                return ''.join(translated_chunks)
            
            return self.translator.translate(clean_text)
        except Exception as e:
            print(f"翻译失败: {e}")
            return text  # 翻译失败时返回原文
    
    def _split_text(self, text: str, max_length: int) -> list:
        """将长文本分割成小块"""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


# 单例实例
translator = Translator()


def translate_text(text: str) -> str:
    """翻译文本的便捷函数"""
    return translator.translate(text)
