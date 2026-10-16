import struct
import unittest
from font_coverage_plan import analyze,cmap,fixture


def sfnt(sub,platform=3,encoding=1,glyphs=100):
    c=struct.pack('>HHHHI',0,1,platform,encoding,12)+sub
    m=struct.pack('>IH',0x00005000,glyphs)
    return struct.pack('>IHHHH',0x10000,2,0,0,0)+struct.pack('>4sIII',b'cmap',0,44,len(c))+struct.pack('>4sIII',b'maxp',0,44+len(c),6)+c+m


def format4(array=False):
    # A -> glyph1, B -> missing. Final U+FFFF sentinel maps to glyph0.
    n=2
    if not array:
        return struct.pack('>7H',4,32,0,4,4,1,0)+struct.pack('>2H',65,65535)+struct.pack('>H',0)+struct.pack('>2H',65,65535)+struct.pack('>2H',(-64)%65536,1)+struct.pack('>2H',0,0)
    return struct.pack('>7H',4,36,0,4,4,1,0)+struct.pack('>2H',66,65535)+struct.pack('>H',0)+struct.pack('>2H',65,65535)+struct.pack('>2H',0,1)+struct.pack('>2H',4,0)+struct.pack('>2H',1,0)


class FontTests(unittest.TestCase):
    def test_full_repertoire_and_zero_glyph(self):
        lookup,meta=cmap(fixture({65:0,0x1F642:2}))
        self.assertEqual((lookup(65),lookup(0x1F642),meta['format']),(0,2,12))

    def test_format4_delta(self):
        lookup,_=cmap(sfnt(format4()))
        self.assertEqual([lookup(c) for c in [64,65,66,65535,0x1F642]],[0,1,0,0,0])

    def test_format4_array_zero_stays_missing(self):
        lookup,_=cmap(sfnt(format4(True)))
        self.assertEqual((lookup(65),lookup(66)),(1,0))

    def test_fallback_greedy_tie_input_order(self):
        r=analyze('ABé🙂',[('latin',fixture({65:1,66:2})),('other',fixture({233:1,0x1F642:2}))])
        self.assertEqual([x['font'] for x in r['greedy_plan']],['latin','other'])
        self.assertEqual(r['uncovered'],[])

    def test_missing_and_frequency(self):
        r=analyze('AAZ',[('a',fixture({65:1}))])
        self.assertEqual(r['uncovered'],['U+005A'])
        self.assertEqual(r['greedy_plan'][0]['new_occurrences'],2)

    def test_controls_ignored_but_spaces_count(self):
        r=analyze('A \n\t\u200d',[('a',fixture({65:1}))])
        self.assertEqual((r['unique_codepoints'],r['uncovered']),(2,['U+0020']))

    def test_no_shaping_or_normalization_assumed(self):
        r=analyze('e\u0301',[('precomposed',fixture({233:1}))])
        self.assertEqual(r['uncovered'],['U+0065','U+0301'])

    def test_glyph_count_checked(self):
        with self.assertRaisesRegex(ValueError,'glyph'):
            cmap(sfnt(format4(),glyphs=1))[0](65)

    def test_truncated_directory_and_tables(self):
        font=fixture({65:1})
        for blob in [b'',b'wOFF'+font[4:],font[:20],font[:-1]]:
            with self.subTest(size=len(blob)),self.assertRaises(ValueError):cmap(blob)

    def test_bad_subtable_offsets(self):
        f=bytearray(fixture({65:1}));struct.pack_into('>I',f,44+8,999999)
        with self.assertRaises(ValueError):cmap(bytes(f))

    def test_preferred_unsupported_format_is_not_silently_replaced(self):
        sub=struct.pack('>HHIII',13,0,16,0,0)
        with self.assertRaisesRegex(ValueError,'unsupported'):
            cmap(sfnt(sub,3,10))

    def test_overlapping_format12_groups(self):
        sub=struct.pack('>HHIII',12,0,40,0,2)+struct.pack('>6I',65,66,1,66,67,1)
        with self.assertRaisesRegex(ValueError,'overlapping'):cmap(sfnt(sub,3,10))

    def test_format4_range_offset_cannot_escape_table(self):
        sub=bytearray(format4(True));struct.pack_into('>H',sub,28,65534)
        with self.assertRaisesRegex(ValueError,'offset'):cmap(sfnt(bytes(sub)))

    def test_duplicate_font_labels_and_empty_corpus(self):
        for text,fonts in [('',[('a',fixture({65:1}))]),('A',[('a',fixture({65:1})),('a',fixture({65:1}))])]:
            with self.assertRaises(ValueError):analyze(text,fonts)

    def test_corpus_and_font_limits(self):
        with self.assertRaises(ValueError):analyze('A',[('a',fixture({65:1}))]*17)
        with self.assertRaises(ValueError):analyze('A'*(2*1024*1024+1),[('a',fixture({65:1}))])

    def test_greedy_cover_does_not_claim_optimality(self):
        # Largest set first needs three fonts although B+C alone covers all six.
        r=analyze('ABCDEF', [('A',fixture({ord(x):i+1 for i,x in enumerate('ABCD')})),('B',fixture({ord(x):i+1 for i,x in enumerate('ABE')})),('C',fixture({ord(x):i+1 for i,x in enumerate('CDF')}))])
        self.assertEqual(len(r['greedy_plan']),3)
        self.assertIn('not shaping',r['scope'])


if __name__=='__main__':unittest.main()
