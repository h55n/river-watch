from pathlib import Path


def test_landing_page_github_button_links_to_repository():
    source = (Path(__file__).parents[1] / "app" / "streamlit_app.py").read_text()

    assert 'st.link_button("GitHub ↗", url="https://github.com/h55n/river-watch"' in source
