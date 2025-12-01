import asyncio
import json
from dotenv import load_dotenv
from backend.app.agents.teacher_agent.critics.fact_critic import (
    CustomFaithfulness, 
    CustomAnswerRelevancy,
    get_fact_critic_llm,
    get_fact_critic_embeddings
)

load_dotenv()

async def test_fact_critic():
    """
    Test Ragas-based Fact Critic with Faithfulness and AnswerRelevancy metrics.
    Uses Ragas v0.3 API with correct row keys.
    """
    print("=== Testing Ragas Fact Critic (v0.3 API) ===\n")
    
    # Initialize LLM using Cook.ai settings
    llm = get_fact_critic_llm()
    embeddings = get_fact_critic_embeddings()
    
    # Initialize metrics and assign LLM
    faithfulness = CustomFaithfulness()
    faithfulness.llm = llm
    
    relevancy = CustomAnswerRelevancy()
    relevancy.llm = llm
    relevancy.embeddings = embeddings  # Required for AnswerRelevancy
    
    # Test Case 1: High quality answer
    print("Test Case 1: High Quality Answer (Faithful & Relevant)")
    print("-" * 60)
    
    row1 = {
        "user_input": "PCA（主成分分析）的主要目的為何？",
        "response": "PCA 的主要用途是將數據降維到較少的主要成分，以簡化數據的分析。",
        "retrieved_contexts": [
            "PCA的主要用途是將數據降維到較少的主要成分，以簡化數據的分析。",
            "主成分分析（PCA）是統計學中常用的降維技術。"
        ]
    }
    
    print(f"Question: {row1['user_input']}")
    print(f"Answer: {row1['response']}")
    print(f"Contexts: {len(row1['retrieved_contexts'])} items\n")
    
    f_result1 = await faithfulness.score_with_feedback(row1)
    r_result1 = await relevancy.score_with_feedback(row1)
    
    print(f"✅ Faithfulness Score: {f_result1['score']:.2f}")
    if f_result1['feedback']:
        for fb in f_result1['feedback']:
            print(f"   - {fb}")
    else:
        print("   - 無問題")
    
    print(f"\n✅ Answer Relevancy Score: {r_result1['score']:.2f}")
    if r_result1['feedback']:
        for fb in r_result1['feedback']:
            print(f"   - {fb}")
    else:
        print("   - 無問題")
    
    # Test Case 2: Low quality answer (unfaithful)
    print("\n\n" + "=" * 60)
    print("Test Case 2: Unfaithful Answer (Contains Unsupported Claims)")
    print("-" * 60)
    
    row2 = {
        "user_input": "PCA（主成分分析）的主要目的為何？",
        "response": "PCA 用於增加數據的維度並提高預測準確性，它是深度學習中最常用的方法。",
        "retrieved_contexts": [
            "PCA的主要用途是將數據降維到較少的主要成分，以簡化數據的分析。"
        ]
    }
    
    print(f"Question: {row2['user_input']}")
    print(f"Answer: {row2['response']}")
    print(f"Contexts: {len(row2['retrieved_contexts'])} items\n")
    
    f_result2 = await faithfulness.score_with_feedback(row2)
    r_result2 = await relevancy.score_with_feedback(row2)
    
    print(f"⚠️  Faithfulness Score: {f_result2['score']:.2f}")
    for fb in f_result2['feedback']:
        print(f"   - {fb}")
    
    print(f"\n⚠️  Answer Relevancy Score: {r_result2['score']:.2f}")
    for fb in r_result2['feedback']:
        print(f"   - {fb}")
    
    # Test Case 3: Off-topic answer
    print("\n\n" + "=" * 60)
    print("Test Case 3: Off-Topic Answer (Low Relevancy)")
    print("-" * 60)
    
    row3 = {
        "user_input": "PCA（主成分分析）的主要目的為何？",
        "response": "機器學習有很多種方法，包括監督學習和非監督學習。常見的算法有決策樹、隨機森林等。",
        "retrieved_contexts": [
            "PCA的主要用途是將數據降維到較少的主要成分，以簡化數據的分析。"
        ]
    }
    
    print(f"Question: {row3['user_input']}")
    print(f"Answer: {row3['response']}")
    print(f"Contexts: {len(row3['retrieved_contexts'])} items\n")
    
    f_result3 = await faithfulness.score_with_feedback(row3)
    r_result3 = await relevancy.score_with_feedback(row3)
    
    print(f"❌ Faithfulness Score: {f_result3['score']:.2f}")
    for fb in f_result3['feedback']:
        print(f"   - {fb}")
    
    print(f"\n❌ Answer Relevancy Score: {r_result3['score']:.2f}")
    for fb in r_result3['feedback']:
        print(f"   - {fb}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_fact_critic())
