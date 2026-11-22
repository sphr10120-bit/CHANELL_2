"""Railway entrypoint: three sources and a linked channel footer."""
import html

import bot

bot.SOURCES.pop("moonmedia", None)
_original_run = bot.run


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


bot.run = run
bot.render = render

if __name__ == "__main__":
    bot.main()
