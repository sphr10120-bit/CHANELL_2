import tempfile
import unittest
from unittest.mock import patch
import bot

class Tests(unittest.TestCase):
    def obj(self):
        return {"title": "تاریخ انتشار بازی اعلام شد", "paragraphs": ["این بند برای آزمایش قالب خبر نوشته شده است.", "این بند دوم برای بررسی قالب خبر نوشته شده است."]}

    def test_render(self):
        text = bot.render(self.obj())
        self.assertTrue(text.startswith("<b>🟦 "))
        self.assertTrue(text.endswith("<b>🆔️ @pixelmediair</b>"))
        self.assertEqual(len(text.split("\n\n")), 4)

    def test_escape(self):
        o = self.obj(); o['title'] = 'خبر بازی <test>'
        self.assertIn('&lt;test&gt;', bot.render(o))

    def test_paragraph_count(self):
        o = self.obj(); o['paragraphs'].append('extra')
        with self.assertRaises(ValueError): bot.render(o)

    def test_title_length(self):
        o = self.obj(); o['title'] = 'الف' * 100
        with self.assertRaises(ValueError): bot.render(o)

    def test_no_urls(self):
        o = self.obj(); o['paragraphs'][0] += ' https://example.com'
        with self.assertRaises(ValueError): bot.render(o)

    def test_dates(self):
        self.assertIsNotNone(bot.timestamp('2026-11-22T10:00:00+03:30'))
        self.assertIsNone(bot.timestamp('not a date'))
        self.assertIsNone(bot.timestamp('2026-11-22T10:00:00'))

    def test_rss(self):
        rows = bot.feed_items('<rss><channel><item><title>A</title><link>https://example.com/a?utm_source=x</link><pubDate>Sun, 22 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>', 'https://example.com')
        self.assertEqual(rows[0]['url'], 'https://example.com/a')
        self.assertIsNotNone(rows[0]['published'])

    def test_atom(self):
        rows=bot.feed_items('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>A</title><link href="https://example.com/a"/><published>2026-11-22T10:00:00Z</published></entry></feed>', 'https://example.com')
        self.assertEqual(len(rows),1)

    def test_baseline_does_not_send(self):
        with tempfile.TemporaryDirectory() as d:
            db = bot.connect(d + '/db')
            with patch.dict(bot.SOURCES, {'test':'https://example.com'}, clear=True), patch.object(bot, 'discover', return_value=[{'url':'https://example.com/a','title':'test','published':None}]), patch.object(bot,'publish') as send:
                bot.run(db)
                self.assertEqual(db.execute('SELECT status FROM articles').fetchone()[0], 'baseline')
                send.assert_not_called()
            db.close()

    def test_start_time_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            db=bot.connect(d+'/db'); first=db.execute("SELECT v FROM meta WHERE k='started'").fetchone()[0]; db.close()
            db=bot.connect(d+'/db'); self.assertEqual(first,db.execute("SELECT v FROM meta WHERE k='started'").fetchone()[0]); db.close()

    def test_no_fallback_on_ambiguous_delivery(self):
        with patch.object(bot,'telegram',side_effect=RuntimeError('unknown')) as send:
            with self.assertRaises(RuntimeError): bot.publish('text','https://example.com/image.jpg')
            self.assertEqual(send.call_count,1)

    def test_image_rejection_falls_back(self):
        with patch.object(bot,'telegram',side_effect=[bot.Rejected(400,'wrong file identifier/HTTP URL specified'),{'message_id':42}]) as send:
            self.assertEqual(bot.publish('text','https://example.com/img'),42)
            self.assertEqual(send.call_count,2)

if __name__ == '__main__': unittest.main()
