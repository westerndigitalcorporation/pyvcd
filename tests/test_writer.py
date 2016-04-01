'''Tests for VCDWriter.'''

from __future__ import print_function
import sys
import pytest

from vcd.writer import VCDWriter, VCDPhaseError, bin_str


def split_lines(capsys):
    return capsys.readouterr()[0].splitlines()


def test_vcd_init(capsys):
    VCDWriter(sys.stdout, date='today')
    VCDWriter(sys.stdout, timescale='1us')
    with pytest.raises(ValueError):
        VCDWriter(sys.stdout, timescale='2 us')
    with pytest.raises(ValueError):
        VCDWriter(sys.stdout, timescale='1 Gs')
    with pytest.raises(TypeError):
        VCDWriter(sys.stdout, timescale=100)
    with pytest.raises(ValueError):
        VCDWriter(sys.stdout, default_scope_type='InVaLiD')


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
    assert lines == ['$timescale 1 us $end',
                     '$enddefinitions $end']
    with pytest.raises(VCDPhaseError):
        vcd.register_int('a', 'b')
    vcd.close()  # Idempotency test
    assert not split_lines(capsys)


def test_vcd_change_after_close(capsys):
    vcd = VCDWriter(sys.stdout, date='')
    var = vcd.register_int('a', 'b')
    assert not split_lines(capsys)
    vcd.close()
    with pytest.raises(VCDPhaseError):
        vcd.change(var, 1, 1)
    with pytest.raises(VCDPhaseError):
        vcd.flush()


def test_vcd_no_scopes(capsys):
    with VCDWriter(sys.stdout,
                   date='today',
                   version='some\nversion',
                   comment='hello'):
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
        var = vcd.register_var('sss', 'nnn', 'integer', 32, ident='foo')
        vcd.change(var, 0, 0)
        vcd.change(var, 1, 10)
    lines = split_lines(capsys)
    assert '$var integer 32 foo nnn $end' in lines
    assert lines[-1] == 'b1010 foo'


def test_vcd_scopes(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        vcd.set_scope_type('eee.fff.ggg', 'task')
        vcd.register_var('aaa.bbb', 'nn0', 'integer', 8, init='z')
        vcd.register_var('aaa.bbb', 'nn1', 'integer', 8)
        vcd.register_var('aaa', 'nn2', 'integer', 8)
        vcd.register_var('aaa.bbb.ccc', 'nn3', 'integer', 8)
        vcd.register_var('aaa.bbb.ddd', 'nn4', 'integer', 8)
        vcd.register_var('eee.fff.ggg', 'nn5', 'integer', 8)
        vcd.set_scope_type('aaa.bbb', 'fork')
        with pytest.raises(TypeError):
            vcd.set_scope_type({'a', 'b', 'c'}, 'module')

    expected_lines = ['$date',
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
                      '$dumpvars',
                      'bz v0',
                      'bx v1',
                      'bx v2',
                      'bx v3',
                      'bx v4',
                      'bx v5',
                      '$end']
    for line, expected in zip(split_lines(capsys), expected_lines):
        print(line, '|', expected)
        assert line.startswith(expected)


def test_vcd_scope_tuple(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        vcd.register_var(('aaa', ), 'nn0', 'integer', 8)
        vcd.register_var(('aaa', 'bbb'), 'nn1', 'integer', 8)
        vcd.register_var('aaa.bbb.ccc', 'nn2', 'integer', 8)
    lines = split_lines(capsys)
    for line, expected in zip(lines, ['$date',
                                      '$timescale',
                                      '$scope module aaa',
                                      '$var',
                                      '$scope module bbb',
                                      '$var',
                                      '$scope module ccc',
                                      '$var']):
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


def test_vcd_change_out_of_order(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        var = vcd.register_var('scope', 'a', 'wire', 1)
        vcd.change(var, 3, True)
        with pytest.raises(VCDPhaseError):
            vcd.change(var, 1, False)


def test_vcd_register_int(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_int('scope', 'a')
    out = capsys.readouterr()[0]
    assert '$var integer 64 v0 a $end' in out
    assert 'bx' in out


def test_vcd_register_real(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_real('scope', 'a')
    out = capsys.readouterr()[0]
    assert '$var real 64 v0 a $end' in out
    assert 'r0' in out


def test_vcd_register_wire(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_wire('scope', 'a')
    out = capsys.readouterr()[0]
    assert '$var wire 1 v0 a $end' in out
    assert 'xv0' in out


def test_vcd_register_reg(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_reg('scope', 'a', 32)
    out = capsys.readouterr()[0]
    assert '$var reg 32 v0 a $end' in out
    assert 'bx v0' in out


def test_vcd_register_event(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        vcd.register_event('scope', 'a')
    out = capsys.readouterr()[0]
    assert '$var event 1 v0 a $end' in out
    assert 'zv0' in out


def test_vcd_scalar_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('aaa', 'nn0', 'integer', 1)
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
    assert lines[-13] == '1v0'
    assert lines[-11] == '0v0'
    assert lines[-9] == 'zv0'
    assert lines[-7] == 'xv0'
    assert lines[-5] == '0v0'
    assert lines[-3] == '1v0'
    assert lines[-1] == 'zv0'


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
    expected_last = ['#1',
                     'r1234.5 v0',
                     'r5432.1 v1',
                     '#2',
                     'r0 v0',
                     'r1 v1',
                     '#3',
                     'r999.9 v0',
                     'r-999.9 v1']

    assert lines[-len(expected_last):] == expected_last


def test_vcd_integer_var(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('aaa', 'nn0', 'integer', 16)
        v1 = vcd.register_var('aaa', 'nn1', 'integer', 8)
        vcd.change(v0, 1, 4)
        vcd.change(v1, 1, -4)
        vcd.change(v0, 2, 'z')
        vcd.change(v1, 2, 'X')
        vcd.change(v1, 3, None)
        with pytest.raises(ValueError):
            vcd.change(v1, 4, -129)
        with pytest.raises(ValueError):
            vcd.change(v1, 4, 'zee')
        with pytest.raises(ValueError):
            vcd.change(v1, 4, 1.234)
    lines = split_lines(capsys)
    assert lines[-8:] == ['#1',
                          'b100 v0',
                          'b11111100 v1',
                          '#2',
                          'bz v0',
                          'bX v1',
                          '#3',
                          'bz v1']


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
        '$var integer 8 v0 a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '$dumpvars',
        'bx v0',
        '$end',
        '#1',
        'b1 v0',
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
        '$var integer 8 v0 a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '$dumpvars',
        'b111 v0',
        '$end',
        '#0',
        '$dumpoff',
        'bx v0',
        '$end',
        '#10',
        '$dumpon',
        'b1 v0',
        '$end',
        '#15',
        'b10 v0',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_dump_off_real(capsys):
    with VCDWriter(sys.stdout, date='') as vcd:
        v0 = vcd.register_real('scope', 'a')
        vcd.change(v0, 1, 1.0)
        vcd.dump_off(2)
        vcd.change(v0, 3, 3.0)
        vcd.dump_on(4)
        vcd.change(v0, 5, 5.0)

    assert v0.ident == 'v0'

    expected_lines = [
        '$timescale 1 us $end',
        '$scope module scope $end',
        '$var real 64 v0 a $end',
        '$upscope $end',
        '$enddefinitions $end',
        '$dumpvars',
        'r0 v0',
        '$end',
        '#1',
        'r1 v0',
        '#2',
        '$dumpoff',
        '$end',
        '#4',
        '$dumpon',
        'r3 v0',
        '$end',
        '#5',
        'r5 v0',
    ]

    assert expected_lines == split_lines(capsys)


def test_vcd_dump_off_on(capsys):
    with VCDWriter(sys.stdout, date='today') as vcd:
        v0 = vcd.register_var('scope', 'a', 'integer', 8)
        v1 = vcd.register_var('scope', 'b', 'wire', 1)

        vcd.change(v0, 1, 10)
        vcd.change(v1, 2, True)

        vcd.dump_off(4)
        vcd.dump_off(5)  # Idempotent

        vcd.change(v0, 6, 11)
        vcd.change(v1, 7, False)

        vcd.dump_on(9)
        vcd.dump_off(10)
        vcd.dump_on(10)

        vcd.change(v0, 11, 12)
        vcd.change(v1, 11, True)


def test_bin_str_3bit():
    bin_u_s = [
        ('0', 0, 0),
        ('1', 1, 1),
        ('10', 2, 2),
        ('11', 3, 3),
        ('100', 4, -4),
        ('101', 5, -3),
        ('110', 6, -2),
        ('111', 7, -1),
    ]
    for expected, unsigned, signed in bin_u_s:
        assert expected == bin_str(unsigned, 3)
        assert expected == bin_str(signed, 3)

    with pytest.raises(ValueError):
        bin_str(8, 3)

    with pytest.raises(ValueError):
        bin_str(-5, 3)
