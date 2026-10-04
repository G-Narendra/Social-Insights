"""Tests for database models and constraints."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Keyword, Mention


class TestKeywordModel:
    """Verify keyword table constraints."""

    @pytest.mark.asyncio
    async def test_create_keyword(self, db_session: AsyncSession) -> None:
        """A keyword can be created and retrieved."""
        kw = Keyword(term="toyota")
        db_session.add(kw)
        await db_session.commit()

        result = await db_session.execute(select(Keyword).where(Keyword.term == "toyota"))
        fetched = result.scalar_one()
        assert fetched.term == "toyota"
        assert fetched.is_tracked is True

    @pytest.mark.asyncio
    async def test_keyword_term_unique(self, db_session: AsyncSession) -> None:
        """Duplicate keyword terms should be rejected."""
        kw1 = Keyword(term="apple")
        kw2 = Keyword(term="apple")
        db_session.add(kw1)
        await db_session.commit()
        db_session.add(kw2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestMentionModel:
    """Verify mention table constraints and upsert behavior."""

    @pytest.mark.asyncio
    async def test_create_mention(self, db_session: AsyncSession) -> None:
        """A mention can be created with required fields."""
        m = Mention(
            keyword_id=1,
            run_id=1,
            source="hackernews",
            source_id="12345",
            text_raw="Toyota just released a new hybrid model",
            status="collected",
        )
        db_session.add(m)
        await db_session.commit()

        result = await db_session.execute(select(Mention))
        fetched = result.scalar_one()
        assert fetched.source == "hackernews"
        assert fetched.status == "collected"

    @pytest.mark.asyncio
    async def test_source_source_id_unique(self, db_session: AsyncSession) -> None:
        """Inserting same (source, source_id) twice should fail."""
        m1 = Mention(
            keyword_id=1,
            run_id=1,
            source="hn",
            source_id="99",
            text_raw="text1",
            status="collected",
        )
        m2 = Mention(
            keyword_id=1,
            run_id=1,
            source="hn",
            source_id="99",
            text_raw="text2",
            status="collected",
        )
        db_session.add(m1)
        await db_session.commit()
        db_session.add(m2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_different_sources_same_id_allowed(self, db_session: AsyncSession) -> None:
        """Same source_id from different sources is fine."""
        m1 = Mention(
            keyword_id=1,
            run_id=1,
            source="hn",
            source_id="99",
            text_raw="text1",
            status="collected",
        )
        m2 = Mention(
            keyword_id=1,
            run_id=1,
            source="reddit",
            source_id="99",
            text_raw="text2",
            status="collected",
        )
        db_session.add_all([m1, m2])
        await db_session.commit()

        result = await db_session.execute(select(Mention))
        assert len(result.scalars().all()) == 2
