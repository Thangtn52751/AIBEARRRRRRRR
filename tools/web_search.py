from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 5):
    """
    Search the web and return summarized results
    """

    results = []

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r["title"],
                    "link": r["href"],
                    "snippet": r["body"]
                })

        return results

    except Exception as e:
        return [{"error": str(e)}]