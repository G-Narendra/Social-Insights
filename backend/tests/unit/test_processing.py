"""
Unit tests for the Data Processing pipeline.
Validates normalization, URL canonicalization, exact/near deduplication,
relevance with ambiguity checks, spam/quality filters, and full 30-mention benchmark.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.processing.canonical_url import canonicalize_url
from app.processing.dedup import Deduplicator, compute_content_hash
from app.processing.normalize import normalize_text, prepare_model_text
from app.processing.pipeline import process_raw_mentions
from app.processing.quality import check_quality
from app.processing.relevance import check_relevance
from app.schemas.mentions import RawMention
from app.services.keyword_service import get_or_create_keyword


class TestNormalization:
    def test_html_stripping_and_entities(self) -> None:
        raw = "<p>Toyota &amp; Lexus announce <b>major</b> recall &#39;immediately&#39;.</p>"
        cleaned = normalize_text(raw)
        assert cleaned == "Toyota & Lexus announce major recall 'immediately'."
        assert "<p>" not in cleaned
        assert "&amp;" not in cleaned

    def test_repeat_collapsing_and_emojis(self) -> None:
        raw = "This car is sooooooo reliable and fast!!!!! 🚗🔥 Absolutely love it!!!!"
        cleaned = normalize_text(raw)
        assert "sooooooo" not in cleaned
        assert "soo" in cleaned
        assert "!!!!!" not in cleaned
        assert "!!" in cleaned
        # Preserves emojis
        assert "🚗" in cleaned
        assert "🔥" in cleaned

    def test_prepare_model_text_tokens(self) -> None:
        raw = "Check out this review by @john_doe on https://example.com/review?id=123 for details"
        model_ready = prepare_model_text(raw)
        assert "<user>" in model_ready
        assert "<url>" in model_ready
        assert "@john_doe" not in model_ready
        assert "https://example.com" not in model_ready


class TestCanonicalURL:
    def test_strip_tracking_params_and_fragments(self) -> None:
        url = "https://WWW.Toyota.com/camry/?utm_source=twitter&utm_medium=social&fbclid=xyz#specs"
        canonical = canonicalize_url(url)
        assert canonical == "https://www.toyota.com/camry"

    def test_strip_default_ports(self) -> None:
        url = "http://example.com:80/articles/toyota/"
        canonical = canonicalize_url(url)
        assert canonical == "http://example.com/articles/toyota"


class TestDeduplication:
    def test_exact_hash_and_url_dedup(self) -> None:
        dedup = Deduplicator()
        text = "Toyota reports quarterly record earnings"
        h = compute_content_hash(text)
        url = "https://example.com/news/1"

        is_dup, reason = dedup.check_duplicate(h, url, text, "1")
        assert is_dup is False

        # Same hash
        is_dup2, reason2 = dedup.check_duplicate(h, "https://example.com/news/2", text, "2")
        assert is_dup2 is True
        assert reason2 == "duplicate_hash"

        # Different hash, same URL
        is_dup3, reason3 = dedup.check_duplicate("hash_diff", url, "Different text here", "3")
        assert is_dup3 is True
        assert reason3 == "duplicate_url"

    def test_near_duplicate_syndication(self) -> None:
        dedup = Deduplicator(near_dedup_threshold=0.8)
        text1 = "Toyota Motor Corporation announced record global production of vehicles today in Tokyo Japan."
        text2 = "Toyota Motor Corporation announced record global production of vehicles today in Tokyo Japan with details."

        h1 = compute_content_hash(text1)
        h2 = compute_content_hash(text2)

        is_dup1, _ = dedup.check_duplicate(h1, None, text1, "1")
        assert is_dup1 is False

        is_dup2, reason2 = dedup.check_duplicate(h2, None, text2, "2")
        assert is_dup2 is True
        assert reason2 == "duplicate_near"


class TestRelevance:
    def test_word_boundary_matching(self) -> None:
        assert check_relevance("I drive a Toyota Camry", None, "Toyota")[0] is True
        # Substring inside another word should NOT match
        assert check_relevance("The toyotathon sale is active", None, "Toyota")[0] is False
        # Alias matching
        assert (
            check_relevance("TM stock price increased today", None, "Toyota", aliases=["TM"])[0]
            is True
        )

    def test_reject_url_only_mention(self) -> None:
        text = "Read the latest vehicle breakdown here: https://example.com/toyota-review"
        is_rel, reason = check_relevance(text, None, "Toyota")
        assert is_rel is False
        assert reason == "irrelevant_url_only"

    def test_ambiguity_disambiguation(self) -> None:
        # Ambiguous brand "Apple"
        tech_text = "Apple released the new M4 MacBook Pro with faster neural engine chips."
        fruit_text = "Grandma baked a delicious apple pie with cinnamon and brown sugar."

        assert (
            check_relevance(
                tech_text, None, "Apple", context_hint="technology consumer electronics"
            )[0]
            is True
        )
        is_rel_fruit, reason_fruit = check_relevance(
            fruit_text, None, "Apple", context_hint="technology consumer electronics"
        )
        assert is_rel_fruit is False
        assert reason_fruit == "irrelevant_ambiguous"


class TestQualityFilters:
    def test_too_short_rejection(self) -> None:
        is_qual, reason, _ = check_quality("Hello car", min_length=15)
        assert is_qual is False
        assert reason == "too_short"

    def test_spam_detection(self) -> None:
        spam = "Claim your free crypto airdrop now at https://t.me/free_tokens_now hurry up!"
        is_qual, reason, _ = check_quality(spam)
        assert is_qual is False
        assert reason == "spam_promo"

    def test_language_filter(self) -> None:
        french = "Toyota annonce une nouvelle voiture électrique très performante en France."
        is_qual, reason, lang = check_quality(french, allowed_languages=["en"])
        assert is_qual is False
        assert reason == "non_english"
        assert lang == "fr"


class TestFullPipelineBenchmark:
    @pytest.mark.asyncio
    async def test_30_mentions_benchmark(self, db_session: AsyncSession) -> None:
        """
        Acceptance requirement: Hand-made set of 30 mentions:
        - 10 good mentions (should be kept)
        - 10 duplicates (should be dropped as duplicate_hash / duplicate_url / duplicate_near)
        - 10 irrelevant/spam/short/non-english (should be dropped)
        Result: exactly 10 kept, 20 dropped.
        """
        kw = await get_or_create_keyword(db_session, "Toyota")

        # 10 Good mentions
        good_mentions = [
            RawMention(
                source="reddit",
                source_id=f"good_{i}",
                title=f"Review {i} of Toyota vehicle",
                text=f"The 2026 Toyota RAV4 hybrid model {i} has excellent fuel efficiency and comfort.",
                keyword="Toyota",
                url=f"https://reddit.com/r/cars/good_{i}",
            )
            for i in range(10)
        ]

        # 10 Duplicate mentions: 5 exact text duplicates (duplicate_hash) + 5 identical URL duplicates (duplicate_url)
        duplicate_mentions = [
            # 5 exact content duplicates
            RawMention(
                source="hackernews",
                source_id=f"dup_hash_{i}",
                title=f"Review {i} of Toyota vehicle",
                text=f"The 2026 Toyota RAV4 hybrid model {i} has excellent fuel efficiency and comfort.",
                keyword="Toyota",
                url=f"https://hackernews.com/item/{i}",
            )
            for i in range(5)
        ] + [
            # 5 identical URL duplicates with different text
            RawMention(
                source="reddit",
                source_id=f"dup_url_{i}",
                title=f"Alternative title {i}",
                text=f"Toyota discussion with alternative text {i} but pointing to same canonical article.",
                keyword="Toyota",
                url=f"https://reddit.com/r/cars/good_{i + 5}",  # same canonical URL as good_5..good_9
            )
            for i in range(5)
        ]

        # 10 Irrelevant / spam / bad quality mentions
        bad_mentions = [
            # 2 URL only
            RawMention(
                source="reddit",
                source_id="bad_1",
                text="Check out this site: https://example.com/toyota-page",
                keyword="Toyota",
            ),
            RawMention(
                source="reddit",
                source_id="bad_2",
                text="Link here https://news.com/toyota-story for more",
                keyword="Toyota",
            ),
            # 2 Keyword missing
            RawMention(
                source="reddit",
                source_id="bad_3",
                text="The Honda Civic gets great fuel economy and handles very well.",
                keyword="Toyota",
            ),
            RawMention(
                source="reddit",
                source_id="bad_4",
                text="Tesla Model Y has improved its suspension dampening significantly.",
                keyword="Toyota",
            ),
            # 2 Too short
            RawMention(source="reddit", source_id="bad_5", text="Toyota!", keyword="Toyota"),
            RawMention(source="reddit", source_id="bad_6", text="Toyota ok", keyword="Toyota"),
            # 2 Spam promo
            RawMention(
                source="reddit",
                source_id="bad_7",
                text="Free giveaway for Toyota fans click here to win $500 cash daily!",
                keyword="Toyota",
            ),
            RawMention(
                source="reddit",
                source_id="bad_8",
                text="Claim free crypto airdrop for Toyota coin at t.me/airdrop",
                keyword="Toyota",
            ),
            # 2 Non-English
            RawMention(
                source="reddit",
                source_id="bad_9",
                text="Toyota annonce une grande mise à jour pour ses moteurs hybrides.",
                keyword="Toyota",
            ),
            RawMention(
                source="reddit",
                source_id="bad_10",
                text="Toyota hat heute die neuen Verkaufszahlen für Elektroautos in Deutschland vorgelegt.",
                keyword="Toyota",
            ),
        ]

        all_30 = good_mentions + duplicate_mentions + bad_mentions

        kept, stats = await process_raw_mentions(
            session=db_session,
            keyword_id=kw.id,
            run_id=1,
            keyword="Toyota",
            raw_mentions=all_30,
        )

        assert len(kept) == 10
        assert stats.total_processed == 30
        assert stats.total_kept == 10
        assert stats.total_dropped == 20

        # Verify all 10 good items are in kept
        kept_ids = {m.source_id for m in kept}
        expected_ids = {f"good_{i}" for i in range(10)}
        assert kept_ids == expected_ids

        # Verify drop reasons are populated
        assert stats.drop_reasons["duplicate_hash"] == 5
        assert stats.drop_reasons["duplicate_url"] == 5
        assert "irrelevant_url_only" in stats.drop_reasons
        assert "irrelevant_keyword" in stats.drop_reasons
        assert "too_short" in stats.drop_reasons
        assert "spam_promo" in stats.drop_reasons
        assert "non_english" in stats.drop_reasons
