import logging
from typing import Dict, List, Any
from ragas.metrics import Faithfulness, AnswerRelevancy
from langchain_openai import ChatOpenAI
import os

logger = logging.getLogger(__name__)

class CustomFaithfulness(Faithfulness):
    """
    Custom Faithfulness metric that generates specific Traditional Chinese feedback.
    Checks if the answer is supported by the retrieved contexts.
    """
    
    async def _ascore(self, row: Dict, callbacks: Any = None) -> float:
        """
        Override _ascore to add custom feedback generation.
        
        Args:
            row: Dict with keys 'user_input', 'response', 'retrieved_contexts'
        """
        # Call parent's _ascore to get the faithfulness score
        score = await super()._ascore(row, callbacks)
        
        # Store score for feedback generation
        self._last_score = score
        
        return score
    
    async def score_with_feedback(self, row: Dict, callbacks: Any = None) -> Dict[str, Any]:
        """
        Computes score and returns detailed feedback in Traditional Chinese.
        
        Args:
            row: Dict with keys:
                - 'user_input': The question
                - 'response': The answer to evaluate
                - 'retrieved_contexts': List of context strings
        
        Returns:
            Dict with 'score' (float) and 'feedback' (List[str])
        """
        try:
            score = await self._ascore(row, callbacks)
            
            feedback = []
            
            # Generate feedback based on score
            if score < 0.5:
                feedback.append("**嚴重問題**: 答案中有多處陳述未得到上下文的支持，可能包含臆測或錯誤資訊。")
                feedback.append("建議：請逐句檢查答案，確保每個陳述都有明確的證據來源。")
            elif score < 0.8:
                feedback.append("**需要改進**: 答案中部分陳述缺乏上下文支持。")
                feedback.append("建議：強化答案與原文的對應關係，移除無法驗證的推論。")
            elif score < 1.0:
                feedback.append("答案大致正確，但仍有少數陳述需要更明確的證據支持。")
                
            return {"score": score, "feedback": feedback}
            
        except Exception as e:
            logger.error(f"Error in CustomFaithfulness evaluation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "score": 0.0, 
                "feedback": [f"評估過程發生錯誤：{str(e)}"]
            }


class CustomAnswerRelevancy(AnswerRelevancy):
    """
    Custom Answer Relevancy metric that generates Traditional Chinese feedback.
    Checks if the answer is relevant to the question.
    """
    
    async def _ascore(self, row: Dict, callbacks: Any = None) -> float:
        """
        Override _ascore to add custom feedback generation.
        
        Args:
            row: Dict with keys 'user_input', 'response', 'retrieved_contexts' (optional)
        """
        # Call parent's _ascore to get the relevancy score
        score = await super()._ascore(row, callbacks)
        
        # Store score for feedback generation
        self._last_score = score
        
        return score
    
    async def score_with_feedback(self, row: Dict, callbacks: Any = None) -> Dict[str, Any]:
        """
        Computes answer relevancy score and returns detailed feedback in Traditional Chinese.
        
        Args:
            row: Dict with keys:
                - 'user_input': The question
                - 'response': The answer to evaluate
                - 'retrieved_contexts': (Optional) List of context strings
        
        Returns:
            Dict with 'score' (float) and 'feedback' (List[str])
        """
        try:
            score = await self._ascore(row, callbacks)
            
            feedback = []
            
            # Generate feedback based on score
            if score < 0.5:
                feedback.append("**嚴重問題**: 答案明顯偏離問題核心，未能直接回答問題。")
                feedback.append("建議：重新聚焦於問題的主要意圖，提供更直接、更相關的答案。")
            elif score < 0.7:
                feedback.append("**需要改進**: 答案部分相關，但包含過多無關資訊或未直接回答問題。")
                feedback.append("建議：精簡答案，移除與問題不直接相關的內容。")
            elif score < 0.9:
                feedback.append("答案基本相關，但可以更精確地回應問題的核心要點。")
                
            return {"score": score, "feedback": feedback}
            
        except Exception as e:
            logger.error(f"Error in CustomAnswerRelevancy evaluation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "score": 0.0,
                "feedback": [f"評估過程發生錯誤：{str(e)}"]
            }


def get_fact_critic_llm() -> ChatOpenAI:
    """
    Get LLM for fact critic using Cook.ai project settings.
    """
    model_name = os.getenv("GENERATOR_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model_name, temperature=0)


def get_fact_critic_embeddings():
    """
    Get embeddings model for AnswerRelevancy metric.
    """
    from langchain_openai import OpenAIEmbeddings
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=embedding_model)
