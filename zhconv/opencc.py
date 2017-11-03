#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import functools
import collections

class PrefixDict(collections.UserDict):
    '''Dict that stores prefixes to speed up lookup'''
    def __setitem__(self, key, item):
        self.data[key] = item
        for ch in range(len(key)):
            wfrag = key[:ch + 1]
            if wfrag not in self.data:
                self.data[wfrag] = None

    def __delitem__(self, key):
        self.data[key] = None

class TextDict(PrefixDict):
    def __init__(self, filename):
        self.data = {}
        with open(filename, 'rb') as f:
            for ln in f:
                sc, tc = ln.strip().decode('utf-8').split('\t')
                self[sc] = tuple(tc.split(' '))

class DictGroup(collections.ChainMap):
    def get(self, key, default=None):
        ret = None
        for mapping in self.maps:
            try:
                # can't use 'key in mapping' with defaultdict
                ret = ret or mapping[key]
            except KeyError:
                pass
        return ret or default

class MaxMatchSegmentation:
    def __init__(self, dictionary):
        self.dic = dictionary

    def __call__(self, s):
        N = len(s)
        pos = 0
        while pos < N:
            i = pos
            frag = s[pos]
            maxword = None
            maxpos = 0
            while i < N and frag in self.dic:
                if self.dic.get(frag):
                    maxword = frag
                    maxpos = i
                i += 1
                frag = s[pos:i+1]
            if maxword is None:
                maxword = s[pos]
                pos += 1
            else:
                pos = maxpos + 1
            yield maxword

class ConversionChain:
    def __init__(self, dictionaries):
        self.dicts = list(dictionaries)

    def __call__(self, segments):
        for seg in segments:
            out = seg
            for d in self.dicts:
                out = d.get(seg) or out
            yield out[0]

def _make_dict(d):
    if d['type'] == 'group':
        return DictGroup(*map(_make_dict, d['dicts']))
    elif d['type'] == 'text':
        key = ('text', d['file'])
        try:
            return _make_dict.dicts[key]
        except KeyError:
            ret = _make_dict.dicts[key] = TextDict(d['file'])
            return ret
    elif d['type'] == 'ocd':
        raise NotImplementedError('ocd file is not supported')
    else:
        raise ValueError('Unknown dictionary type: ' + d['type'])

_make_dict.dicts = {}

def _make_segmentation(d):
    if d['type'] == 'mmseg':
        return MaxMatchSegmentation(_make_dict(d['dict']))
    else:
        raise ValueError('Unknown segmentation type: ' + d['type'])

class ZhConverter:

    def __init__(self, config):
        self.name = config['name']
        self.seg = _make_segmentation(config['segmentation'])
        self.convchain = ConversionChain(_make_dict(d['dict']) for d in config['conversion_chain'])

    @classmethod
    def fromjson(cls, fp):
        config = json.load(fp)
        return cls(config)

    def __call__(self, s):
        print(tuple(self.seg(s)))
        return ''.join(self.convchain(self.seg(s)))
