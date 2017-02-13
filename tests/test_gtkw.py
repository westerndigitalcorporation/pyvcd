"""Tests for vcd.gtkw module."""

from __future__ import print_function
import datetime
import os
import time

import pytest
import six

from vcd.gtkw import GTKWSave, decode_flags, make_translation_filter


def test_decode_flags():
    assert decode_flags('@200') == ['blank']
    assert decode_flags('200') == ['blank']
    assert decode_flags(0x200) == ['blank']
    assert decode_flags('@802023') == [
        'highlight', 'hex', 'rjustify', 'ftranslated', 'grp_begin']


def test_gtkw_comments(gtkw):
    gtkw.comment('Hi', 'abc', 'def')
    lines = gtkw.file.getvalue().splitlines()
    assert lines == ['[*] Hi', '[*] abc', '[*] def']


def test_gtkw_dumpfile(gtkw):
    gtkw.dumpfile('/foo/bar')
    assert gtkw.file.getvalue() == '[dumpfile] "{}"\n'.format(
        os.path.abspath('/foo/bar'))


def test_gtkw_dumpfile_none(gtkw):
    gtkw.dumpfile(None)
    assert gtkw.file.getvalue() == '[dumpfile] (null)\n'


def test_gtkw_dumpfile_noabspath(gtkw):
    gtkw.dumpfile('foo', abspath=False)
    assert gtkw.file.getvalue() == '[dumpfile] "foo"\n'


def test_gtkw_dumpfile_mtime(gtkw):
    with pytest.raises(Exception):  # FileNotFoundError or IOError
        gtkw.dumpfile_mtime(dump_path='InVaLiD')
    gtkw.dumpfile_mtime(mtime=1234567890.0)
    assert (gtkw.file.getvalue() ==
            '[dumpfile_mtime] "Fri Feb 13 23:31:30 2009"\n')


def test_gtkw_dumpfile_mtime_gmtime(gtkw):
    with pytest.raises(Exception):  # FileNotFoundError or IOError
        gtkw.dumpfile_mtime(dumpfile='InVaLiD')
    with pytest.raises(TypeError):
        gtkw.dumpfile_mtime(mtime='right now')
    gtkw.dumpfile_mtime(mtime=time.gmtime(1234567890.0))
    assert (gtkw.file.getvalue() ==
            '[dumpfile_mtime] "Fri Feb 13 23:31:30 2009"\n')


def test_gtkw_dumpfile_mtime_datetime(gtkw):
    with pytest.raises(Exception):  # FileNotFoundError or IOError
        gtkw.dumpfile_mtime('InVaLiD')
    gtkw.dumpfile_mtime(mtime=datetime.datetime(2009, 2, 13, 23, 31, 30))
    assert (gtkw.file.getvalue() ==
            '[dumpfile_mtime] "Fri Feb 13 23:31:30 2009"\n')


def test_gtkw_dumpfile_size(gtkw):
    gtkw.dumpfile_size(1234)
    assert gtkw.file.getvalue() == '[dumpfile_size] 1234\n'


def test_gtkw_dumpfile_size_path(gtkw, tmpdir):
    dump_file = tmpdir.join('test.dump')
    dump_file.write('x')
    gtkw.dumpfile_size(dump_path=str(dump_file))
    assert gtkw.file.getvalue() == '[dumpfile_size] 1\n'


def test_gtkw_savefile_noname(gtkw):
    gtkw.savefile()
    assert gtkw.file.getvalue() == "[savefile] (null)\n"


def test_gtkw_savefile_none():
    sio = six.StringIO()
    sio.name = '/some/path'
    gtkw = GTKWSave(sio)
    gtkw.savefile()
    assert sio.getvalue() == '[savefile] "{}"\n'.format(
        os.path.abspath('/some/path'))


def test_gtkw_savefile_path(gtkw):
    gtkw.savefile('/foo/bar')
    assert gtkw.file.getvalue() == '[savefile] "{}"\n'.format(
        os.path.abspath('/foo/bar'))


def test_gtkw_savefile_noabs(gtkw):
    gtkw.savefile('foo/bar', abspath=False)
    assert gtkw.file.getvalue() == '[savefile] "foo/bar"\n'


def test_gtkw_timestart_default(gtkw):
    gtkw.timestart()
    assert gtkw.file.getvalue() == '[timestart] 0\n'


def test_gtkw_zoom_markers(gtkw):
    gtkw.zoom_markers(marker=17, z=999)
    assert gtkw.file.getvalue() == '*0.000000 17' + (' -1' * 25) + ' 999\n'


def test_gtkw_size(gtkw):
    gtkw.size(123, 456)
    assert gtkw.file.getvalue() == '[size] 123 456\n'


def test_gtkw_pos(gtkw):
    gtkw.pos(123, -1)
    assert gtkw.file.getvalue() == '[pos] 123 -1\n'


def test_gtkw_treeopen(gtkw):
    gtkw.treeopen('a.b.')
    gtkw.treeopen('a.b.c')
    assert gtkw.file.getvalue().splitlines() == [
        '[treeopen] a.b.',
        '[treeopen] a.b.c.']  # '.' added


def test_gtkw_signals_width(gtkw):
    gtkw.signals_width(1234)
    assert gtkw.file.getvalue() == '[signals_width] 1234\n'


def test_gtkw_sst_expanded(gtkw):
    gtkw.sst_expanded(True)
    assert gtkw.file.getvalue() == '[sst_expanded] 1\n'


def test_gtkw_pattern_trace(gtkw):
    gtkw.pattern_trace(False)
    assert gtkw.file.getvalue() == '[pattern_trace] 0\n'


def test_gtkw_group(gtkw):
    with gtkw.group('mygroup'):
        gtkw.trace('a.b.c', alias='C', color=3)
        gtkw.trace('a.b.d')

    lines = gtkw.file.getvalue().splitlines()
    assert lines == [
        '@800200',
        '-mygroup',
        '@22',
        '[color] 3',
        '+{C} a.b.c',
        'a.b.d',
        '@1000200',
        '-mygroup']


def test_gtkw_group_closed(gtkw):
    with gtkw.group('mygroup', closed=True):
        gtkw.trace('a.b.c', alias='C', color=3)
        gtkw.trace('a.b.d')

    lines = gtkw.file.getvalue().splitlines()
    assert lines == [
        '@c00200',
        '-mygroup',
        '@22',
        '[color] 3',
        '+{C} a.b.c',
        'a.b.d',
        '@1401200',
        '-mygroup']


def test_gtkw_group_highlight(gtkw):
    with gtkw.group('mygroup', highlight=True):
        gtkw.trace('a.b.c', alias='C', color=3)
        gtkw.trace('a.b.d')

    lines = gtkw.file.getvalue().splitlines()
    assert lines == [
        '@800201',
        '-mygroup',
        '@22',
        '[color] 3',
        '+{C} a.b.c',
        'a.b.d',
        '@1000201',
        '-mygroup']


def test_gtkw_blank(gtkw):
    gtkw.blank()
    assert gtkw.file.getvalue() == '@200\n-\n'


def test_gtkw_blank_highlight(gtkw):
    gtkw.blank(highlight=True)
    assert gtkw.file.getvalue() == '@201\n-\n'


def test_gtkw_blanks(gtkw):
    gtkw.blank()
    gtkw.blank()
    gtkw.blank()
    assert gtkw.file.getvalue() == '@200\n-\n-\n-\n'


def test_gtkw_analog_extension(gtkw):
    gtkw.trace('a.b.c', datafmt='real')
    gtkw.blank(analog_extend=True)

    lines = gtkw.file.getvalue().splitlines()
    assert lines == ['@40020', 'a.b.c', '@20200', '-']


def test_gtkw_labels(gtkw):
    gtkw.blank('hi')
    gtkw.blank('ho')
    assert gtkw.file.getvalue() == '@200\n-hi\n-ho\n'


def test_gtkw_invalid_datafmt(gtkw):
    with pytest.raises(ValueError):
        gtkw.trace('a.b.c', datafmt='InVaLiD')


def test_gtkw_trace_highlight(gtkw):
    gtkw.trace('a.b.c', highlight=True, rjustify=False)
    assert gtkw.file.getvalue() == '@3\na.b.c\n'


def test_gtkw_trace_extraflags(gtkw):
    gtkw.trace('a.b.c', datafmt='real', extraflags=['analog_step',
                                                    'analog_fullscale'])
    assert gtkw.file.getvalue() == '@c8020\na.b.c\n'


def test_gtkw_trace_filter_files(gtkw):
    gtkw.trace('mod.a', translate_filter_file='filter1.txt')
    gtkw.trace('mod.b', translate_filter_file='filter2.txt')
    gtkw.trace('mod.c', translate_filter_file='filter1.txt')
    lines = gtkw.file.getvalue().splitlines()

    assert lines == ['@2022',
                     '^1 filter1.txt',
                     'mod.a',
                     '^2 filter2.txt',
                     'mod.b',
                     '^1 filter1.txt',
                     'mod.c']


def test_gtkw_trace_filter_proc(gtkw):
    gtkw.trace('a.b.c', translate_filter_proc='filter.exe')
    assert gtkw.file.getvalue() == '@4022\n^>1 filter.exe\na.b.c\n'


def test_gtkw_trace_bits(gtkw):
    name = 'a.b.c[3:0]'
    with gtkw.trace_bits(name):
        gtkw.trace_bit(0, name, alias='bit0', color=0)
        gtkw.trace_bit(1, name, alias='bit1')
        gtkw.trace_bit(2, name, color='yellow')
        gtkw.trace_bit(3, name)

    lines = gtkw.file.getvalue().splitlines()

    assert lines == [
        '@22',
        'a.b.c[3:0]',
        '@28',
        '[color] 0',
        '+{bit0} (0)a.b.c[3:0]',
        '+{bit1} (1)a.b.c[3:0]',
        '[color] 3',
        '(2)a.b.c[3:0]',
        '(3)a.b.c[3:0]',
        '@1001200',
        '-group_end']


def test_gtkw_trace_bits_highlight(gtkw):
    name = 'a.b.c[3:0]'
    with gtkw.trace_bits(name, highlight=True, rjustify=False):
        gtkw.trace_bit(0, name, alias='bit0', color=0)
        gtkw.trace_bit(1, name, alias='bit1')
        gtkw.trace_bit(2, name, color=2)
        gtkw.trace_bit(3, name)

    lines = gtkw.file.getvalue().splitlines()

    assert lines == [
        '@3',
        'a.b.c[3:0]',
        '@9',
        '[color] 0',
        '+{bit0} (0)a.b.c[3:0]',
        '+{bit1} (1)a.b.c[3:0]',
        '[color] 2',
        '(2)a.b.c[3:0]',
        '(3)a.b.c[3:0]',
        '@1001201',
        '-group_end']


def test_gtkw_trace_bits_extra(gtkw):
    name = 'a.b.c[1:0]'
    with gtkw.trace_bits(name, extraflags=['invert']):
        gtkw.trace_bit(0, name, alias='bit0', color='cycle')
        gtkw.trace_bit(1, name, alias='bit1', color='cycle')

    lines = gtkw.file.getvalue().splitlines()

    assert lines == [
        '@62',
        'a.b.c[1:0]',
        '@68',
        '[color] 1',
        '+{bit0} (0)a.b.c[1:0]',
        '[color] 2',
        '+{bit1} (1)a.b.c[1:0]',
        '@1001200',
        '-group_end']


def test_gtkw_color_stack(gtkw):
    gtkw.trace('a', color='cycle')
    gtkw.trace('b', color='cycle')
    with gtkw.group('mygroup'):
        gtkw.trace('x', color='cycle')
        gtkw.trace('y', color='cycle')
        gtkw.trace('z', color='cycle')
    gtkw.trace('c', color='cycle')
    gtkw.trace('d', color='cycle')

    lines = gtkw.file.getvalue().splitlines()

    assert lines == [
        '@22',
        '[color] 1',
        'a',
        '[color] 2',
        'b',
        '@800200',
        '-mygroup',
        '@22',
        '[color] 1',
        'x',
        '[color] 2',
        'y',
        '[color] 3',
        'z',
        '@1000200',
        '-mygroup',
        '@22',
        '[color] 3',
        'c',
        '[color] 4',
        'd']


def test_xlate_filter():
    xlatef = make_translation_filter(size=8, translations=[
        (16, "Sixteen", "Magenta"),
        (32, "Thirty-two"),
        (-128, "Negative"),
        (255, "Two Five Five", "Blue"),
    ])

    assert xlatef.splitlines() == ['10 ?Magenta?Sixteen',
                                   '20 Thirty-two',
                                   '80 Negative',
                                   'ff ?Blue?Two Five Five']


def test_xlate_filter_size():
    with pytest.raises(ValueError):
        # 8 does not fit in 3-bits.
        make_translation_filter(size=3, datafmt='oct',
                                translations=[(8, 'Eight', 'Red')])


def test_xlate_filter_datafmt():
    with pytest.raises(ValueError):
        make_translation_filter(size=8, datafmt='InVaLiD',
                                translations=[(8, 'Eight', 'Red')])


def test_xlate_filter_bin():
    xlatef = make_translation_filter(size=2, datafmt='bin', translations=[
        (0, "Zero"),
        (1, "One"),
        (2, "Two"),
    ])

    assert xlatef.splitlines() == ['00 Zero', '01 One', '10 Two']


def test_xlate_filter_decimal():
    xlatef = make_translation_filter(datafmt='dec', translations=[
        (1, "X"),
        (1234, "XXXX"),
        (123456789, "XXXXXXXXX"),
    ])

    assert xlatef.splitlines() == ['1 X', '1234 XXXX', '123456789 XXXXXXXXX']


def test_xlate_filter_ascii():
    xlatef = make_translation_filter(datafmt='ascii', translations=[
        ('a', 'Aye'),
        ('+', 'Plus', 'Red'),
        ('!', 'Bang'),
        (35, 'Pound', 'Blue'),
    ])

    assert xlatef.splitlines() == [
        'a Aye',
        '+ ?Red?Plus',
        '! Bang',
        '# ?Blue?Pound']


def test_xlate_filter_invalid_ascii():
    with pytest.raises(ValueError):
        make_translation_filter(datafmt='ascii', translations=[('abc', 'ABC')])

    with pytest.raises(TypeError):
        make_translation_filter([(35.0, 'Pound')], datafmt='ascii')


def test_xlate_filter_real():
    xlatef = make_translation_filter(datafmt='real', translations=[
        (123, 'One two three'),
        (44.0, 'Forty-four'),
        (1.23, 'One point two three'),
        (-17.5, 'Sub zero'),
    ])

    assert xlatef.splitlines() == [
        '123 One two three',
        '44 Forty-four',
        '1.23 One point two three',
        '-17.5 Sub zero']
