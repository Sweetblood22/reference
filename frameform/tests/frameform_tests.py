# -*- coding: utf-8 -*-
"""
Created on Wed May 31 08:42:54 2017

@author: jmccrary
"""


import unittest as ut
from ipywidgets import (Button, Checkbox, HBox, VBox, Layout, 
                        IntText, FloatText, Text)
from frameform.frameform import _type_to_widget

int_DTYPES = ['int{:d}'.format(2**x) for x in range(3, 7)] + ['int']
uint_DTYPES = ['uint{:d}'.format(2**x) for x in range(3, 7)] + ['uint']
float_DTYPES = ['float{:d}'.format(2**x) for x in range(4, 7)] + ['float']
other_DTYPES = ['object']


class Test_type_to_widget(ut.TestCase):
    def test_floats(self):
        for dname in float_DTYPES:
            self.assertIs(_type_to_widget(dname), FloatText)
            
    def test_ints(self):
        for dname in int_DTYPES:
            self.assertIs(_type_to_widget(dname), IntText)
        for dname in uint_DTYPES:
            self.assertIs(_type_to_widget(dname), IntText)
    
    def test_text(self):
        for dname in other_DTYPES:
            self.assertEqual(_type_to_widget(dname), Text)
            
    def test_bool(self):
        self.assertEqual(_type_to_widget('bool'), Checkbox)
    
if __name__ == '__main__':
    ut.main()
