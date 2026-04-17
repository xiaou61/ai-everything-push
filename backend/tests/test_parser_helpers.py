from app.services.parsers import extract_nested_value, html_to_text


def test_extract_nested_value_supports_dot_path_and_list_index() -> None:
    payload = {
        "data": {
            "items": [
                {"title": "first"},
                {"title": "second"},
            ]
        }
    }

    assert extract_nested_value(payload, "data.items.1.title") == "second"


def test_html_to_text_strips_tags_and_collapses_whitespace() -> None:
    html = """
    <article>
      <h1>Article title</h1>
      <p>First paragraph.</p>
      <p>Second paragraph with <strong>bold</strong> text.</p>
    </article>
    """

    text = html_to_text(html)

    assert text == "Article title First paragraph. Second paragraph with bold text."
