'''Tests for VCDWriter.'''

import os
import sys
import timeit

import pytest

from vcd.common import Timescale, TimescaleMagnitude, TimescaleUnit
from vcd.writer import (
    CompoundVectorVariable,
    ScopeType,
    Variable,
    VCDPhaseError,
    VCDWriter,
    VectorVariable,
)


def split_lines(capsys):
    return capsys.readouterr()[0].splitlines()


def test_vcd_init(capsys):
    VCDWriter(sys.stdout, date='today')
    with pytest.raises(ValueError):
        VCDWriter(sys.stdout, default_scope_type='InVaLiD')


@pytest.mark.parametrize(
    'timescale, expected',
    [
        ('1 us', '1 us'),
        ('us', '1 us'),
        ((1, 'ns'), '1 ns'),
        ('100ps', '100 ps'),
        ((TimescaleMagnitude.ten, TimescaleUnit.femtosecond), '10 fs'),
        (Timescale(TimescaleMagnitude.hundred, TimescaleUnit.millisecond), '100 ms'),
    ],
)
def test_vcd_timescales(capsys, timescale, expected):
    with VCDWriter(sys.stdout, date='', timescale=timescale):
        pass
    lines = split_lines(capsys)
    assert lines == ['$timescale {} $end'.format(expected), '$enddefinitions $end']


@pytest.mark.parametrize(
    'timescale, exc_type',
    [
        ('2 us', ValueError),
        ('1 Gs', ValueError),
        ((), ValueError),
        (('1', 'ns'), ValueError),
        ((1, 'us', 'ns'), ValueError),
        (100, TypeError),
    ],
)
def test_vcd_timescale_invalid(capsys, timescale, exc_type):
    with pytest.raises(exc_type):
        VCDWriter(sys.stdout, timescale=timescale)


def test_vcd_init_empty_date(capsys):
    with VCDWriter(sys.stdout, date=''):
        pass
    assert '$date' not in capsys.readouterr()[0]


def test_vcd_init_none_date(capsys):
    with VCDWriter(sys.stdout, date=None):
        pass
    assert '$date' in capsys.readouterr()[0]


def test_vcd_flush(capsys):
    vcd = VCDWriter(sys.stdout, date='today')
    assert not split_lines(capsys)
    vcd.flush(17)
    lines = split_lines(capsys)
    assert lines[-1] == '#17'


def test_vcd_close(capsys):
    vcd = VCDWriter(sys.stdout, date='')
    assert not split_lines(capsys)
    vcd.close()
    lines = split_lines(capsys)
    assert lines == ['$timescale 1 us $end', '$enddefinitions $end']
    with pytest.raises(VCDPhaseError):
        vcd.register_var('a', 'b', 'integer')
    vcd.close()  # Idempotency test
    assert not split_lines(capsys)


def test_vcd_change_after_close(capsys):
    vcd = VCDWriter(sys.stdout, date='')
    var = vcd.register_var('a', 'b', 'integer')
    assert not split_lines(capsys)
    vcd.close()
    with pytest.raises(VCDPhaseError):
        vcd.change(var, 1, 1)
    with pytest.raises(VCDPhaseError):
        vcd.flush()


def test_vcd_alias_after_close(capsys):
    vcd = VCDWriter(sys.stdout)
    var = vcd.register_var('a', 'b', 'integer')
    assert not split_lines(capsys)
    vcd.close()
    with pytest.raises(VCDPhaseError):
        vcd.register_alias('c', 'd', var)


def test_vcd_no_scopes(capsys):
    with VCDWriter(sys.stdout, date='today', version='some\nversion', comment='hello'):
        pass
    lines = split_lines(capsys)
    expected_lines = [
        '$comment hello $end',
        '$date today $end',
        '$timescale 1 us $end',
        '$version',
        '\tsome',
        '\tversion',
        '$end',
        '$enddefinitions $end',
    ]
    assert expected_lines == lines


def test_vcd_one_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        var = vcd.register_var('sss', 'nnn', 'integer', 32)
        vcd.change(var, 0, 0)
        vcd.change(var, 1, 10)
    lines = split_lines(capsys)
    assert '$var integer 32 ! nnn $end' in lines
    assert lines[-1] == 'b1010 !'


def test_vcd_invalid_vector_init():
    with VCDWriter(sys.stdout) as vcd:
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'a', 'integer', 8, init='eight')
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'b', 'integer', 8, init=8.0)


def test_vcd_no_duplicates(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        var = vcd.register_var('sss', 'nnn', 'integer', 32)
        vcd.change(var, 0, 'x')
        vcd.change(var, 1, 10)
        vcd.change(var, 2, 10)
        vcd.change(var, 3, 10)
        vcd.change(var, 4, 15)
        vcd.change(var, 5, 15)
        vcd.change(var, 6, 10)
    assert split_lines(capsys) == [
        '$date today $end',
        '$timescale 1 us $end',
        '$scope module sss $end',
        '$var integer 32 ! nnn $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'bx !',
        '$end',
        '#1',
        'b1010 !',
        '#4',
        'b1111 !',
        '#6',
        'b1010 !',
    ]


def test_vcd_aliases(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        var = vcd.register_var('sss', 'nnn', 'integer', 32)
        vcd.register_alias('sss', 'mmm', var)
        vcd.register_alias('ttt', 'nnn', var)
        vcd.change(var, 0, 'x')
        vcd.change(var, 1, 10)
        vcd.change(var, 2, 11)
    assert split_lines(capsys) == [
        '$date today $end',
        '$timescale 1 us $end',
        '$scope module sss $end',
        '$var integer 32 ! nnn $end',
        '$var integer 32 ! mmm $end',
        '$upscope $end',
        '$scope module ttt $end',
        '$var integer 32 ! nnn $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'bx !',
        '$end',
        '#1',
        'b1010 !',
        '#2',
        'b1011 !',
    ]


def test_vcd_scopes(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        vcd.set_scope_type('eee.fff.ggg', ScopeType.task)
        vcd.register_var('aaa.bbb', 'nn0', 'integer', 8, init='z')
        vcd.register_var('aaa.bbb', 'nn1', 'integer', 8)
        vcd.register_var('aaa', 'nn2', 'integer', 8)
        vcd.register_var('aaa.bbb.ccc', 'nn3', 'integer', 8)
        vcd.register_var('aaa.bbb.ddd', 'nn4', 'integer', 8)
        vcd.register_var('eee.fff.ggg', 'nn5', 'integer', 8)
        vcd.set_scope_type('aaa.bbb', 'fork')
        with pytest.raises(TypeError):
            vcd.set_scope_type({'a', 'b', 'c'}, 'module')

    expected_lines = [
        '$date',
        '$timescale',
        '$scope module aaa',
        '$var',
        '$scope fork bbb',
        '$var',
        '$var',
        '$scope module ccc',
        '$var',
        '$upscope',
        '$scope module ddd',
        '$var',
        '$upscope',
        '$upscope',
        '$upscope',
        '$scope module eee',
        '$scope module fff',
        '$scope task ggg',
        '$var',
        '$upscope',
        '$upscope',
        '$upscope',
        '$enddefinitions',
        '#0',
        '$dumpvars',
        'bz !',
        'bx "',
        'bx #',
        'bx $',
        'bx %',
        'bx &',
        '$end',
    ]
    for line, expected in zip(split_lines(capsys), expected_lines):
        print(line, '|', expected)
        assert line.startswith(expected)


def test_vcd_init_timestamp(capsys):
    with VCDWriter(sys.stdout, date='today', init_timestamp=123) as vcd:
        vcd.register_var('a', 'n', 'integer', 8, init='z')

    expected_lines = [
        '$date',
        '$timescale',
        '$scope module a',
        '$var integer 8 ! n $end',
        '$upscope',
        '$enddefinitions',
        '#123',
        '$dumpvars',
        'bz !',
        '$end',
    ]
    for line, expected in zip(split_lines(capsys), expected_lines):
        print(line, '|', expected)
        assert line.startswith(expected)


def test_vcd_scope_tuple(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        vcd.register_var(('aaa',), 'nn0', 'integer', 8)
        vcd.register_var(('aaa', 'bbb'), 'nn1', 'integer', 8)
        vcd.register_var('aaa.bbb.ccc', 'nn2', 'integer', 8)
    lines = split_lines(capsys)
    for line, expected in zip(
        lines,
        [
            '$date',
            '$timescale',
            '$scope module aaa',
            '$var',
            '$scope module bbb',
            '$var',
            '$scope module ccc',
            '$var',
        ],
    ):
        assert line.startswith(expected)


def test_vcd_late_registration(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        var0 = vcd.register_var('aaa.bbb', 'nn0', 'integer', 8)
        vcd.change(var0, 0, 123)

        # Still at t0, registration okay...
        vcd.register_var('aaa.bbb', 'nn1', 'integer', 8)

        vcd.change(var0, 1, 210)

        with pytest.raises(VCDPhaseError):
            vcd.register_var('aaa.bbb', 'nn2', 'integer', 8)


def test_vcd_late_alias_registration(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        var0 = vcd.register_var('aaa.bbb', 'nn0', 'integer', 8)
        vcd.change(var0, 0, 123)

        # Still at t0, registration okay...
        vcd.register_alias('aaa.bbb', 'nn1', var0)

        vcd.change(var0, 1, 210)

        with pytest.raises(VCDPhaseError):
            vcd.register_alias('aaa.bbb', 'nn2', var0)


def test_vcd_missing_size(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        with pytest.raises(ValueError):
            vcd.register_var('a.b.c', 'name', 'wire', size=None)


def test_vcd_invalid_var_type(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        with pytest.raises(ValueError):
            vcd.register_var('aaa.bbb', 'nn0', 'InVaLiD', 8)


def test_vcd_invalid_scope_type(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        with pytest.raises(ValueError):
            vcd.set_scope_type('aaa.bbb', 'InVaLiD')


def test_vcd_duplicate_var_name(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        vcd.register_var('aaa.bbb', 'nn0', 'integer', 8)
        with pytest.raises(KeyError):
            vcd.register_var('aaa.bbb', 'nn0', 'wire', 1)


def test_vcd_duplicate_alias(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        var = vcd.register_var('aaa.bbb', 'nn0', 'integer', 8)
        vcd.register_alias('aaa.bbb', 'nn1', var)
        with pytest.raises(KeyError):
            vcd.register_alias('aaa.bbb', 'nn0', var)
        with pytest.raises(KeyError):
            vcd.register_alias('aaa.bbb', 'nn1', var)


def test_vcd_change_out_of_order(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        var = vcd.register_var('scope', 'a', 'wire', 1)
        vcd.change(var, 3, True)
        with pytest.raises(VCDPhaseError):
            vcd.change(var, 1, False)


def test_vcd_register_int(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_var('scope', 'a', 'integer')
    out = capsys.readouterr()[0]
    assert '$var integer 64 ! a $end' in out
    assert 'bx !' in out


def test_vcd_register_int_tuple(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_var('scope', 'a', 'integer', (8, 4, 1))
    out = capsys.readouterr()[0]
    assert '$var integer 13 ! a $end' in out
    assert 'bx !' in out


def test_vcd_register_int_tuple_invalid_init_type():
    with VCDWriter(sys.stdout, date='') as vcd:
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'a', 'integer', (8, 4, 1), 0)


def test_vcd_register_int_tuple_invalid_init_len():
    with VCDWriter(sys.stdout, date='') as vcd:
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'a', 'integer', (8, 4, 1), (0, 0, 0, 0))


def test_vcd_register_int_tuple_invalid_init_values():
    with VCDWriter(sys.stdout, date='') as vcd:
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'a', 'integer', (8, 4, 1), (1.0, 0, 0))


def test_vcd_register_real(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_var('scope', 'a', 'real')
        vcd.register_var('scope', 'b', 'real', init=123)
        vcd.register_var('scope', 'c', 'real', init=1.23)
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'f', 'real', init='real')

    expected_last = [
        '$scope module scope $end',
        '$var real 64 ! a $end',
        '$var real 64 " b $end',
        '$var real 64 # c $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'r0 !',
        'r123 "',
        'r1.23 #',
        '$end',
    ]
    lines = split_lines(capsys)
    assert lines[-len(expected_last) :] == expected_last


def test_vcd_register_event(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_var('scope', 'a', 'event')
        vcd.register_var('scope', 'b', 'event', init=True)
        with pytest.raises(ValueError):
            vcd.register_var('scope', 'f', 'event', init='yes')
    expected_last = [
        '$scope module scope $end',
        '$var event 1 ! a $end',
        '$var event 1 " b $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        '$end',
    ]
    lines = split_lines(capsys)
    assert lines[-len(expected_last) :] == expected_last


def test_vcd_bad_event():
    with VCDWriter(sys.stdout, date='') as vcd:
        var = vcd.register_var('scope', 'a', 'event')
        vcd.change(var, 1, True)
        with pytest.raises(ValueError):
            vcd.change(var, 2, False)


def test_vcd_multiple_events(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        var = vcd.register_var('scope', 'a', 'event')
        vcd.change(var, 1, True)
        vcd.change(var, 2, True)
        vcd.change(var, 2, True)
        vcd.change(var, 2, True)
        vcd.change(var, 3, True)

    expected_lines = [
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var event 1 ! a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        '$end',
        '#1',
        '1!',
        '#2',
        '1!',
        '1!',
        '1!',
        '#3',
        '1!',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_scalar_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('aaa', 'nn0', 'integer', 1)
        vcd.register_var('aaa', 'nn1', 'integer', 1, False)
        with pytest.raises(ValueError):
            vcd.register_var('aaa', 'fff', 'integer', 1, init=1.23)
        vcd.change(v0, 1, True)
        vcd.change(v0, 2, False)
        vcd.change(v0, 3, 'z')
        vcd.change(v0, 4, 'x')
        vcd.change(v0, 5, 0)
        vcd.change(v0, 6, 1)
        with pytest.raises(ValueError):
            vcd.change(v0, 7, 'bogus')
        vcd.change(v0, 7, None)
    lines = split_lines(capsys)
    expected = [
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'x!',
        '0"',
        '$end',
        '#1',
        '1!',
        '#2',
        '0!',
        '#3',
        'z!',
        '#4',
        'x!',
        '#5',
        '0!',
        '#6',
        '1!',
        '#7',
        'z!',
    ]
    assert lines[-len(expected) :] == expected


def test_vcd_real_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('aaa', 'nn0', 'real', 32)
        v1 = vcd.register_var('aaa', 'nn1', 'real', 64)
        vcd.change(v0, 1, 1234.5)
        vcd.change(v1, 1, 5432.1)
        vcd.change(v0, 2, 0)
        vcd.change(v1, 2, 1)
        vcd.change(v0, 3, 999.9)
        vcd.change(v1, 3, -999.9)
        with pytest.raises(ValueError):
            vcd.change(v0, 4, 'z')
        with pytest.raises(ValueError):
            vcd.change(v0, 4, 'x')
        with pytest.raises(ValueError):
            vcd.change(v0, 4, 'InVaLiD')
    lines = split_lines(capsys)
    expected_last = [
        '#1',
        'r1234.5 !',
        'r5432.1 "',
        '#2',
        'r0 !',
        'r1 "',
        '#3',
        'r999.9 !',
        'r-999.9 "',
    ]

    assert lines[-len(expected_last) :] == expected_last


def test_vcd_integer_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('aaa', 'nn0', 'integer', 16)
        v1 = vcd.register_var('aaa', 'nn1', 'integer', 8)
        vcd.change(v0, 1, 4)
        vcd.change(v1, 1, -4)
        vcd.change(v0, 2, 'z')
        vcd.change(v1, 2, 'X')
        vcd.change(v1, 3, None)
        vcd.change(v0, 3, '1010')
        with pytest.raises(ValueError):
            vcd.change(v1, 4, -129)
        with pytest.raises(ValueError):
            vcd.change(v1, 4, '111100001')  # Too long
        with pytest.raises(ValueError):
            vcd.change(v1, 4, 1.234)

    expected_last = [
        '#1',
        'b100 !',
        'b11111100 "',
        '#2',
        'bz !',
        'bX "',
        '#3',
        'bz "',
        'b1010 !',
    ]

    lines = split_lines(capsys)
    assert lines[-len(expected_last) :] == expected_last


def test_vcd_dump_on_no_op(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('scope', 'a', 'integer', 8)
        vcd.dump_on(0)  # Should be a no-op
        vcd.change(v0, 1, 1)
        vcd.dump_on(2)  # Also a no-op

    expected_lines = [
        '$date today $end',
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var integer 8 ! a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'bx !',
        '$end',
        '#1',
        'b1 !',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_dump_off_early(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('scope', 'a', 'integer', 8, init=7)
        vcd.dump_off(0)
        vcd.change(v0, 5, 1)
        vcd.dump_on(10)
        vcd.change(v0, 15, 2)

    expected_lines = [
        '$date today $end',
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var integer 8 ! a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'b111 !',
        '$end',
        '$dumpoff',
        'bx !',
        '$end',
        '#10',
        '$dumpon',
        'b1 !',
        '$end',
        '#15',
        'b10 !',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_dump_off_real(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        v0 = vcd.register_var('scope', 'a', 'real')
        vcd.change(v0, 1, 1.0)
        vcd.dump_off(2)
        vcd.change(v0, 3, 3.0)
        vcd.dump_on(4)
        vcd.change(v0, 5, 5.0)

    assert v0.ident == '!'

    expected_lines = [
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var real 64 ! a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'r0 !',
        '$end',
        '#1',
        'r1 !',
        '#2',
        '$dumpoff',
        '$end',
        '#4',
        '$dumpon',
        'r3 !',
        '$end',
        '#5',
        'r5 !',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_dump_off_on(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('scope', 'a', 'integer', 8)
        v1 = vcd.register_var('scope', 'b', 'wire', 1)
        v2 = vcd.register_var('scope', 'c', 'event')
        v3 = vcd.register_var('scope', 'd', 'real', init=1.23)

        vcd.change(v0, 1, 10)
        vcd.change(v1, 2, True)

        vcd.dump_off(4)
        vcd.dump_off(5)  # Idempotent

        vcd.change(v0, 6, 11)
        vcd.change(v1, 7, False)
        vcd.change(v2, 8, True)  # should not show up in next dump

        vcd.dump_on(9)
        vcd.dump_off(10)
        vcd.dump_on(10)

        vcd.change(v0, 11, 12)
        vcd.change(v1, 11, True)
        vcd.change(v3, 11, 3.21)

    expected_lines = [
        '$date today $end',
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var integer 8 ! a $end',
        '$var wire 1 " b $end',
        '$var event 1 # c $end',
        '$var real 64 $ d $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'bx !',
        'x"',
        'r1.23 $',
        '$end',
        '#1',
        'b1010 !',
        '#2',
        '1"',
        '#4',
        '$dumpoff',
        'bx !',
        'x"',
        '$end',
        '#9',
        '$dumpon',
        'b1011 !',
        '0"',
        'r1.23 $',
        '$end',
        '#10',
        '$dumpoff',
        'bx !',
        'x"',
        '$end',
        '$dumpon',
        'b1011 !',
        '0"',
        'r1.23 $',
        '$end',
        '#11',
        'b1100 !',
        '1"',
        'r3.21 $',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_dump_off_time_order(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('scope', 'a', 'integer', 8)
        vcd.dump_off(1)

        with pytest.raises(VCDPhaseError):
            vcd.dump_off(0)

        assert v0.value == 'x'
        vcd.change(v0, 1, 10)

    expected_lines = [
        '$date today $end',
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var integer 8 ! a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'bx !',
        '$end',
        '#1',
        '$dumpoff',
        'bx !',
        '$end',
    ]

    assert expected_lines == split_lines(capsys)


def test_variable():
    var = Variable('ident0', 'integer', 16, 0)
    with pytest.raises(NotImplementedError):
        var.format_value(0)


@pytest.mark.parametrize(
    'expected, unsigned, signed',
    [
        ('b0 v', 0, 0),
        ('b1 v', 1, 1),
        ('b10 v', 2, 2),
        ('b11 v', 3, 3),
        ('b100 v', 4, -4),
        ('b101 v', 5, -3),
        ('b110 v', 6, -2),
        ('b111 v', 7, -1),
    ],
)
def test_vector_var_3bit(expected, unsigned, signed):
    var = VectorVariable('v', 'integer', 3, unsigned)
    assert expected == var.format_value(unsigned)
    assert expected == var.format_value(signed)


def test_vector_var_3bit_invalid():
    var = VectorVariable('v', 'integer', 3, 0)

    with pytest.raises(ValueError):
        var.format_value(8)

    with pytest.raises(ValueError):
        var.format_value(-5)


@pytest.mark.parametrize(
    'size, value, expected',
    [
        ((8, 4, 1), (0, 0, 0), 'b0 v'),
        ((8, 4, 1), (1, 0, 0), 'b100000 v'),
        ((8, 4, 1), (0, 0, 1), 'b1 v'),
        ((8, 4, 1), (1, 1, 1), 'b100011 v'),
        ((8, 4, 1), ('z', 'x', '-'), 'bzxxxx- v'),
        ((8, 4, 1), ('0', '1', None), 'b1z v'),
        ((8, 4, 1), (0xF, 0, 1), 'b111100001 v'),
        ((8, 4, 1), (None, 'x', None), 'bzxxxxz v'),
        ((8,), (1,), 'b1 v'),
        ((8, 32), (0b1010, 0xFF00FF00), 'b101011111111000000001111111100000000 v'),
    ],
)
def test_compound_vector(size, value, expected):
    var = CompoundVectorVariable('v', 'integer', size, value)
    assert expected == var.format_value(value)


@pytest.mark.parametrize(
    'size, value', [((1, 2, 3), (0, 0)), ((1, 2, 3), (0, 0, 0, 0)), ((1,), (0, 0))]
)
def test_compound_vector_invalid_values(size, value):
    var = CompoundVectorVariable('v', 'integer', size, None)
    with pytest.raises(ValueError):
        var.format_value(value)


def test_dump_off_compound_vector(capsys):
    with VCDWriter(sys.stdout) as vcd:
        v0 = vcd.register_var('aaa', 'n0', 'integer', size=(4, 4, 8), init=None)
        vcd.register_var('aaa', 'n1', 'integer', size=(4, 4, 8), init=('z', 'x', '-'))
        vcd.register_var('aaa', 'n2', 'integer', size=(1, 1), init=(True, False))
        v3 = vcd.register_var('aaa', 'n3', 'integer', size=(1, 2, 3), init='xxx')
        with pytest.raises(ValueError):
            vcd.register_var('aaa', 'n4', 'integer', size=(1, 2, 3), init=(1, 2))
        vcd.change(v0, 1, (0, 0, 0))
        vcd.change(v0, 2, (15, 0, 0xFF))
        vcd.dump_off(3)
        vcd.change(v3, 4, '1-1')
        vcd.dump_on(5)
    expected = [
        '$var integer 16 ! n0 $end',
        '$var integer 16 " n1 $end',
        '$var integer 2 # n2 $end',
        '$var integer 6 $ n3 $end',
        '$upscope $end',
        '$enddefinitions $end',
        '#0',
        '$dumpvars',
        'bx !',
        'bzxxxx-------- "',
        'b10 #',
        'bx $',
        '$end',
        '#1',
        'b0 !',
        '#2',
        'b1111000011111111 !',
        '#3',
        '$dumpoff',
        'bx !',
        'bx "',
        'bx #',
        'bx $',
        '$end',
        '#5',
        '$dumpon',
        'b1111000011111111 !',
        'bzxxxx-------- "',
        'b10 #',
        'b1--001 $',
        '$end',
    ]
    lines = split_lines(capsys)
    assert expected == lines[-len(expected) :]


def test_vcd_string_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('aaa', 'nn0', 'string')
        vcd.register_var('aaa', 'nn1', 'string', init='foobar')
        with pytest.raises(ValueError):
            vcd.register_var('aaa', 'fff', 'string', init=123)
        vcd.change(v0, 1, 'hello')
        vcd.change(v0, 2, '')
        vcd.change(v0, 3, 'world')
        vcd.change(v0, 4, 'spaces are\tok')
        vcd.change(v0, 5, 'newlines\r\ntoo')
        vcd.change(v0, 6, 'slash\\slash')
        vcd.change(v0, 7, None)
        vcd.change(v0, 8, '!')
        with pytest.raises(ValueError) as e:
            vcd.change(v0, 9, 42)
        assert 'Invalid string value' in e.value.args[0]
        vcd.dump_off(8)
    expected = [
        '#0',
        '$dumpvars',
        's !',
        'sfoobar "',
        '$end',
        '#1',
        'shello !',
        '#2',
        's !',
        '#3',
        'sworld !',
        '#4',
        'sspaces\\x20are\\tok !',
        '#5',
        'snewlines\\r\\ntoo !',
        '#6',
        'sslash\\\\slash !',
        '#7',
        's !',
        '#8',
        's! !',
        '$dumpoff',
        '$end',
    ]
    lines = split_lines(capsys)
    assert expected == lines[-len(expected) :]


def test_execution_speed():
    """Manual test for how fast we can write to a VCD file

    See https://github.com/westerndigitalcorporation/pyvcd/issues/9

    pytest -vvs -k test_execution_speed

    """
    t0 = timeit.default_timer()
    with open(os.devnull, 'w') as f:
        with VCDWriter(f, timescale=(10, 'ns'), date='today') as writer:
            counter_var = writer.register_var('a.b.c', 'counter', 'integer', size=8)
            compound_var = writer.register_var(
                'a.b.c', 'compound', 'integer', size=(1, 3, 4)
            )
            for i in range(1000, 300000, 300):
                for timestamp, value in enumerate(range(10, 200, 2)):
                    writer.change(counter_var, i + timestamp, value)
                    writer.change(
                        compound_var,
                        i + timestamp,
                        (timestamp & 0b1, timestamp & 0b111, timestamp & 0b1111),
                    )
    elapsed = timeit.default_timer() - t0
    print('Elapsed:', elapsed)
