"""
Enrich mentions with local ML models (sentiment + topic).
Moves mentions from 'relevant' to 'done'.
"""

import asyncio
from sqlalchemy import select
from app.db.session import init_db, get_session_factory, close_db
from app.db.models import Mention
from app.ml.sentiment import analyze_sentiment_batch
from app.ml.topics import classify_topics_batch


async def main():
    await init_db()
    factory = get_session_factory()
    
    async with factory() as session:
        query = select(Mention).where(Mention.status == "relevant")
        res = await session.execute(query)
        mentions = list(res.scalars().all())
        print(f"Found {len(mentions)} relevant mentions to enrich...")
        
        if not mentions:
            print("No relevant mentions found.")
            await close_db()
            return
            
        texts = [m.text_clean or m.text_raw or "" for m in mentions]
        
        print("1. Running local Twitter-RoBERTa sentiment prediction (batch_size=32)...")
        sentiments = analyze_sentiment_batch(texts, batch_size=32)
        
        print("2. Running local MiniLM topic classification (batch_size=32)...")
        topics = classify_topics_batch(texts)
        
        print("3. Updating records in database...")
        for m, s, t in zip(mentions, sentiments, topics):
            m.sentiment = s.label
            m.sentiment_score = s.score
            m.sentiment_confidence = s.score
            m.sentiment_model = "twitter-roberta-base-sentiment-latest"
            m.topic = t.topic
            m.topic_confidence = t.score
            m.topic_model = "all-MiniLM-L6-v2"
            m.secondary_topic = t.secondary_topic
            m.status = "done"
            
        await session.commit()
        print(f"Successfully enriched {len(mentions)} mentions to status='done'!")
        
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
