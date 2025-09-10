#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  9 11:40:15 2025

@author: katedamato
"""

from dash import html, dcc
print(html.Div()._prop_names)       # properties Div accepts
print(dcc.Input()._prop_names)      # properties Input accepts
print(dcc.Dropdown()._prop_names)   # properties Dropdown accepts

print(app._prop_names)
