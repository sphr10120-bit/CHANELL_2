"""Railway entrypoint: Gamefa, Zoomg and Vigiato only."""
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


bot.run = run

if __name__ == "__main__":
    bot.main()
