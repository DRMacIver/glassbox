import os
import glassbox
import pytest
import chardet

corpus = [bytearray()] + [bytearray([i]) for i in xrange(256)]


def test_detecting_novel_corpus_elements_for_chardet(benchmark):
    @benchmark
    def result():
        novelty = glassbox.NoveltyDetector()
        for c in corpus:
            glassbox.begin()
            chardet.detect(c)
            novelty.novel(glassbox.collect())
    assert result is None

def test_running_chardet_on_whole_corpus_without_glassbox(benchmark):
    @benchmark
    def result():
        for c in corpus:
            chardet.detect(c)
    assert result is None


def test_running_chardet_on_whole_corpus_under_glassbox(benchmark):
    @benchmark
    def result():
        glassbox.begin()
        for c in corpus:
            chardet.detect(c)
        glassbox.collect()
    assert result is None
