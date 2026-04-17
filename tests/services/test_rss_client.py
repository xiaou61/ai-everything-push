from __future__ import annotations

from app.services.crawler.rss_client import parse_feed_entries


def test_parse_rss_entries():
    raw_xml = """
    <rss version="2.0">
      <channel>
        <title>Example Feed</title>
        <item>
          <title>Example article</title>
          <link>https://example.com/articles/1</link>
          <pubDate>Fri, 17 Apr 2026 09:00:00 GMT</pubDate>
          <author>team@example.com</author>
        </item>
        <item>
          <title>Another article</title>
          <link>https://example.com/articles/2</link>
        </item>
      </channel>
    </rss>
    """
    entries = parse_feed_entries(raw_xml)
    assert len(entries) == 2
    assert entries[0].title == "Example article"
    assert entries[0].link == "https://example.com/articles/1"

