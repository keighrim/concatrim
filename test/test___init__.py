import unittest
import concatrim


class TestConcatrimmer(unittest.TestCase):

    def setUp(self):
        self.pruner = concatrim.Concatrimmer('../README.md', 100)
        
    def test_is_overlapping(self):
        self.assertFalse(self.pruner.is_overlapping((1, 2), (3, 4)))
        self.assertFalse(self.pruner.is_overlapping((3, 4), (1, 2)))
        self.assertTrue(self.pruner.is_overlapping((1, 3), (2, 4)))
        self.assertTrue(self.pruner.is_overlapping((1, 4), (2, 3)))

    def test_add_spans(self):
        self.pruner.add_spans([1, 2])
        self.assertEqual(1, len(self.pruner._span_ori_starts))
        self.assertEqual(1, len(self.pruner._span_ori_ends))
        self.pruner._empty_spans()
        self.pruner.add_spans([1, 2], [100, 200])
        self.assertEqual(2, len(self.pruner._span_ori_starts))
        self.assertEqual(2, len(self.pruner._span_ori_ends))
        self.pruner._empty_spans()
        self.pruner.add_spans([100, 200], [10, 20])
        self.assertEqual(2, len(self.pruner._span_ori_starts))
        self.assertEqual(2, len(self.pruner._span_ori_ends))
        
        with self.assertRaises(ValueError):
            self.pruner.add_spans([0, 10], [1, 4])
        with self.assertRaises(ValueError):
            self.pruner.add_spans([1, 4], [0, 10])
        self.pruner._empty_spans()

    def test_convert_wo_trim(self):
        query = 500
        self.assertEqual(query, self.pruner.conv_to_trimmed(query))
        self.assertEqual(query, self.pruner.conv_to_original(query))
        
    def test_convert(self):
        self.pruner.pad_len = 100
        self.pruner.add_spans((100, 200))
        self.pruner.add_spans((300, 400))
        self.pruner.add_spans((500, 600))
        self.assertEqual(self.pruner.conv_to_trimmed(150), 50)
        self.assertEqual(self.pruner.conv_to_trimmed(250), None)
        self.assertEqual(self.pruner.conv_to_trimmed(50), None)
        self.assertEqual(self.pruner.conv_to_original(50), 150)
        self.assertEqual(self.pruner.conv_to_original(150), None)
        self.assertEqual(self.pruner.conv_to_original(450), 550)
        
        self.pruner.pad_len = 0
        self.assertEqual(self.pruner.conv_to_trimmed(150), 50)
        self.assertEqual(self.pruner.conv_to_trimmed(450), None)
        self.assertEqual(self.pruner.conv_to_trimmed(50), None)
        self.assertEqual(self.pruner.conv_to_original(50), 150)
        self.assertEqual(self.pruner.conv_to_original(150), 350)

    def test_concatrim(self):
        self.pruner.pad_len = 100
        self.pruner.add_spans((100, 200))
        self.pruner.add_spans((300, 400))
        self.pruner.add_spans((500, 600))
        print(self.pruner.concatrim('non-existing', dryrun=True))
 

if __name__ == '__main__':
    unittest.main()
