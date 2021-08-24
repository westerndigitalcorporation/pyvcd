"""Tests for vcd.reader."""

import io
from textwrap import dedent

import pytest

from vcd.common import ScopeType, Timescale, TimescaleMagnitude, TimescaleUnit, VarType
from vcd.reader import (
    RealChange,
    ScalarChange,
    ScopeDecl,
    StringChange,
    TokenKind,
    VarDecl,
    VCDParseError,
    VectorChange,
    tokenize,
)


def test_parse_comment():
    tokens = tokenize(io.BytesIO(b'$comment hello $end'))
    token = next(tokens)
    assert token.comment == 'hello'


def test_parse_multiline_comment():
    tokens = tokenize(io.BytesIO(b'$comment\nhello\nworld\n$end'))
    token = next(tokens)
    assert token.comment == 'hello\nworld'


def test_parse_date():
    tokens = tokenize(io.BytesIO(b'$date\nnow!!! $end'))
    token = next(tokens)
    assert token.date == 'now!!!'


def test_parse_date_with_bad_end():
    tokens = tokenize(io.BytesIO(b'$date\nnow!!!$end'))
    with pytest.raises(VCDParseError) as e:
        next(tokens)
    assert str(e.value).startswith('2:6: ')


def test_parse_enddefinitions():
    tokens = tokenize(io.BytesIO(b'$comment hi $end $enddefinitions $end'))
    token = next(tokens)
    assert token.comment == 'hi'
    token = next(tokens)
    assert token.kind == TokenKind.ENDDEFINITIONS


def test_parse_junk_in_enddefinitions():
    tokens = tokenize(io.BytesIO(b'$comment hi $end $enddefinitions $var $end'))
    token = next(tokens)
    assert token.comment == 'hi'
    with pytest.raises(VCDParseError) as e:
        next(tokens)
    assert e.value.args[0].startswith('1:35: Expected $end')


def test_parse_scope_decl():
    tokens = tokenize(io.BytesIO(b'$scope module foobar $end'))
    token = next(tokens)
    assert token.scope.type_.value == 'module'
    assert token.scope.ident == 'foobar'


def test_parse_var_decl():
    tokens = tokenize(io.BytesIO(b'$var integer 8 ! foo [17] $end'))
    token = next(tokens)
    assert token.var.type_ == VarType.integer
    assert token.var.ref_str == 'foo[17]'


def test_parse_var_decl_with_dotted_ref():
    tokens = tokenize(io.BytesIO(b'$var real  1  aaaaa  SomeThing.MORE_STUFF_0  $end'))
    token = next(tokens)
    assert token.var.type_ == VarType.real
    assert token.var.ref_str == 'SomeThing.MORE_STUFF_0'


def test_time_change():
    tokens = tokenize(io.BytesIO(b'#1234'))
    token = next(tokens)
    assert token.time_change == 1234


def test_scalar_change():
    tokens = tokenize(io.BytesIO(b'1!"$"'))
    token = next(tokens)
    assert token.scalar_change.id_code == '!"$"'
    assert token.scalar_change.value == '1'


def test_vector_change():
    tokens = tokenize(io.BytesIO(b'b1X1z   abc'))
    token = next(tokens)
    assert token.vector_change.id_code == 'abc'
    assert token.vector_change.value == '1X1z'


@pytest.mark.parametrize("buf_size", range(1, 400))
def test_comprehensive(buf_size):
    vcd = """\
        $comment Test VCD $end
        $date the present day $end
        $timescale 10 ps $end
        $scope module alpha $end
        $scope fork beta $end
        $var wire 1  ! a_scalar $end
        $var integer 8 " b_vector $end
        $upscope $end
        $var real 64 # c_real $end
        $var string 1 $ d_string $end
        $upscope $end
        $enddefinitions $end
        #0
        $dumpvars
        1!
        b1010 "
        r12.34 #
        shello $
        $end
        #17
        0!
        #42
        b1zzz "
        #50
        r1e-10 #
        #999
        sbye $
        $comment
        Fin.
        $end

        """
    tokens = tokenize(io.BytesIO(dedent(vcd).encode('ascii')), buf_size)
    assert next(tokens).comment == 'Test VCD'
    assert next(tokens).date == 'the present day'
    assert next(tokens).timescale == Timescale(
        TimescaleMagnitude.ten, TimescaleUnit.picosecond
    )
    assert next(tokens).scope == ScopeDecl(ScopeType.module, 'alpha')
    assert next(tokens).scope == ScopeDecl(ScopeType.fork, 'beta')
    assert next(tokens).var == VarDecl(VarType.wire, 1, '!', 'a_scalar', None)
    assert next(tokens).var == VarDecl(VarType.integer, 8, '"', 'b_vector', None)
    assert next(tokens).kind is TokenKind.UPSCOPE
    assert next(tokens).var == VarDecl(VarType.real, 64, '#', 'c_real', None)
    assert next(tokens).var == VarDecl(VarType.string, 1, '$', 'd_string', None)
    assert next(tokens).kind is TokenKind.UPSCOPE
    assert next(tokens).kind is TokenKind.ENDDEFINITIONS
    assert next(tokens).time_change == 0
    assert next(tokens).kind is TokenKind.DUMPVARS
    assert next(tokens).scalar_change == ScalarChange('!', '1')
    assert next(tokens).vector_change == VectorChange('"', 10)
    assert next(tokens).real_change == RealChange('#', 12.34)
    assert next(tokens).string_change == StringChange('$', 'hello')
    assert next(tokens).kind is TokenKind.END
    assert next(tokens).time_change == 17
    assert next(tokens).scalar_change == ScalarChange('!', '0')
    assert next(tokens).time_change == 42
    assert next(tokens).vector_change == VectorChange('"', '1zzz')
    assert next(tokens).time_change == 50
    assert next(tokens).real_change == RealChange('#', 1e-10)
    assert next(tokens).time_change == 999
    assert next(tokens).string_change == StringChange('$', 'bye')
    assert next(tokens).comment == 'Fin.'
    with pytest.raises(StopIteration):
        next(tokens)
