def register() -> dict:
    return {
        "name": "ui_design_assist",
        "description": "Provides assistance with front-end UI/UX design tasks, including color palette generation, font suggestions, and layout ideas.",
        "version": "1.0.0",
        "author": "M.I.L.L.A.",
        "commands": ["/design"],
    }

def execute(payload: dict) -> dict:
    try:
        from web_search import web_search  # Import here to avoid circular dependencies
        from youtube_search import youtube_search

        query = payload.get("query", "UI design best practices")
        design_type = payload.get("type", "general")  # e.g., "mobile", "desktop", "web"

        if not query:
            return {"ok": False, "error": "Missing query parameter."}

        if design_type == "color_palette":
            search_term = f"{query} color palette"
            results = web_search(search_term)
            if results:
                return {"ok": True, "result": f"Here are some color palette suggestions based on '{query}':\n{results}"}
            else:
                return {"ok": False, "error": "No color palettes found for that query."}

        elif design_type == "font_suggestions":
            search_term = f"{query} font pairings"
            results = web_search(search_term)
            if results:
                return {"ok": True, "result": f"Here are some font pairing suggestions for '{query}':\n{results}"}
            else:
                return {"ok": False, "error": "No font pairings found for that query."}

        elif design_type == "layout_ideas":
            search_term = f"{query} UI layout examples"
            results = web_search(search_term)
            if results:
                return {"ok": True, "result": f"Here are some layout ideas for '{query}':\n{results}"}
            else:
                return {"ok": False, "error": "No layout ideas found for that query."}

        elif design_type == "tutorial":
            search_term = f"{query} UI design tutorial"
            youtube_results = youtube_search(search_term, max_results=3)
            if youtube_results:
                video_links = "\n".join([f"{title}: {url}" for title, url in youtube_results])
                return {"ok": True, "result": f"Here are some YouTube tutorials for '{query}':\n{video_links}"}
            else:
                return {"ok": False, "error": "No YouTube tutorials found for that query."}

        else:
            general_results = web_search(query)
            if general_results:
                return {"ok": True, "result": f"Here are some general UI/UX design resources for '{query}':\n{general_results}"}
            else:
                return {"ok": False, "error": "No results found for that query."}

    except Exception as e:
        return {"ok": False, "error": str(e)}