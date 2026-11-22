"""Railway entrypoint: three sources, linked footer, and a gaming-news filter."""
import html
import json
import re

import bot

bot.SOURCES.pop("moonmedia", None)
_original_run = bot.run
_original_summarize = bot.summarize


def run(db, dry=False):
    # Preserve history while preventing queued Moonmedia articles from being sent.
    db.execute(
        "UPDATE articles SET status='disabled_source' "
        "WHERE source='moonmedia' AND status IN ('pending','retry')"
    )
    db.commit()
    return _original_run(db, dry)


def render(obj):
    bot.validate_content(obj)
    title = html.escape(obj["title"])
    p1, p2 = map(html.escape, obj["paragraphs"])
    footer = '<i><a href="https://t.me/pixelmediair">🔷 pixel media</a></i>'
    return f"<b>🟦 {title}</b>\n\n{p1}\n\n{p2}\n\n{footer}"


def summarize(data, recent):
    # Make the gaming decision explicit and prevent the model from rejecting
    # gaming news merely because a film, show, or anime is also mentioned.
    data = dict(data)
    data["classification_rules"] = [
        "Accept if the main subject is a video game, game studio, publisher,",
        "console, platform, gaming hardware, esports, gaming industry,",
        "game adaptation, or a game-related announcement.",
        "Do not reject gaming news solely because a film, TV show, anime,",
        "actor, director, or streaming service is mentioned.",
        "Reject only when the main subject is exclusively cinema, television,",
        "anime, a guide, a review, or another non-gaming topic.",
        "When uncertain, set is_gaming_news=true only if a clear gaming subject",
        "exists; otherwise set it to false.",
    ]
    return _original_summarize(data, recent)


bot.run = run
bot.render = render
bot.summarize = summarize

if __name__ == "__main__":
    bot.main()
