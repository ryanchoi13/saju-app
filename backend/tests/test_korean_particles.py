import unittest
from app.engine.korean import josa


class KoreanParticlesTest(unittest.TestCase):
    def test_templates(self):
        cases = [('시계','을/를','시계를'),('가방','을/를','가방을'),
                 ('네이비','과/와','네이비와'),('블랙','과/와','블랙과'),
                 ('스카이블루','으로/로','스카이블루로'),('실버','으로/로','실버로'),
                 ('하늘','으로/로','하늘로'),('검정','으로/로','검정으로'),
                 ('변화','이/가','변화가'),('재정비','은/는','재정비는'),
                 ('시계','이며/며','시계며'),('가방','이며/며','가방이며'),
                 ('시계]','을/를','시계]를'),('3','은/는','3은')]
        for word, pair, expected in cases:
            with self.subTest(word=word,pair=pair):
                self.assertEqual(josa(word,pair),expected)

    def test_empty(self):
        self.assertEqual(josa('', '은/는'),'')
