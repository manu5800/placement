#! /usr/bin/env python
# -*- coding: utf-8 -*-

from utilities import *
import unittest

class TestNumTaskToLetter(unittest.TestCase):

#    def setUp(self):
#        self.seq = range(10)

    def test_normal(self):
        self.assertEqual(numTaskToLetter(0),'A')
        self.assertEqual(numTaskToLetter(25),'Z')
        self.assertEqual(numTaskToLetter(26),'a')
        self.assertEqual(numTaskToLetter(51),'z')
        self.assertEqual(numTaskToLetter(52),'0')
        self.assertEqual(numTaskToLetter(61),'9')

        

    def test_out_of_limits(self):
        self.assertRaises(PlacementException, numTaskToLetter, -1)
        self.assertRaises(PlacementException, numTaskToLetter, 62)

class TestList2CompactString(unittest.TestCase):
    def setUp(self):
        self.s1 = [0,1,2,5,6,7,9]
        self.s11= [6,5,0,1,9,7,2]
        self.s2 = []
        self.s3 = [0]
        self.s4 = [1,1,9]

    def test_normal(self):
        self.assertEqual(list2CompactString(self.s1),'0-2,5-7,9')
        self.assertEqual(list2CompactString(self.s11),'0-2,5-7,9')

        # s11 a été trié par l'appel précédent
#        self.assertEqual(self.s1,self.s11)

    def test_limits(self):
        self.assertEqual(list2CompactString(self.s2),'')
        self.assertEqual(list2CompactString(self.s3),'0')
        self.assertEqual(list2CompactString(self.s4),'1,9')
        

class TestCompactString2List(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(compactString2List('0-3,5'),[0,1,2,3,5])
        self.assertEqual(compactString2List('5,2,0,1'),[5,2,0,1])

    def test_limits(self):
        self.assertEqual(compactString2List(''),[])
        self.assertEqual(compactString2List('1'),[1])
        self.assertEqual(compactString2List('3-1'),[1,2,3])
        self.assertRaises(ValueError,compactString2List,'a-c')

        
#    def test_shuffle(self):
#        # make sure the shuffled sequence does not lose any elements
#        random.shuffle(self.seq)
#        self.seq.sort()
#        self.assertEqual(self.seq, range(10))

#    def test_choice(self):
#        element = random.choice(self.seq)
#        self.assertTrue(element in self.seq)

#    def test_sample(self):
#        self.assertRaises(ValueError, random.sample, self.seq, 20)
#        for element in random.sample(self.seq, 5):
#            self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest.main()
