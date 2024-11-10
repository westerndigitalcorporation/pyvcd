"""Read Value Change Dump (VCD) files.

The primary interface is the :func:`tokenize()` generator function,
parses a binary VCD stream, yielding tokens as they are encountered.

.. code::

   >>> import io
   >>> from vcd.reader import TokenKind, tokenize
   >>> vcd = b"$date today $end $timescale 1 ns $end"
   >>> tokens = tokenize(io.BytesIO(vcd))
   >>> token = next(tokens)
   >>> assert token.kind is TokenKind.DATE
   >>> assert token.date == "today"
   >>> token = next(tokens)
   >>> assert token.kind is TokenKind.TIMESCALE
   >>> assert token.timescale.magnitude.value == 1
   >>> assert token.timescale.unit.value == "ns"

"""

import io
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, NamedTuple, Optional, Tuple, Union

from vcd.common import ScopeType, Timescale, TimescaleMagnitude, TimescaleUnit, VarType


class TokenKind(Enum):
    """Kinds of VCD tokens."""

    COMMENT = 1
    DATE = 2
    ENDDEFINITIONS = 3
    SCOPE = 4
    TIMESCALE = 5
    UPSCOPE = 6
    VAR = 7
    VERSION = 8
    DUMPALL = 9
    DUMPOFF = 10
    DUMPON = 11
    DUMPVARS = 12
    END = 13
    CHANGE_TIME = 14
    CHANGE_SCALAR = 15
    CHANGE_VECTOR = 16
    CHANGE_REAL = 17
    CHANGE_STRING = 18


class VarDecl(NamedTuple):
    """VCD variable declaration.

    Examples::

       $var wire 4 !@# foobar [ 3 : 1 ] $end
       $var real 1 aaa foobar $end
       $var integer 32 > foobar[8] $end

    """

    type_: VarType  #: Type of variable
    size: int  #: Size, in bits, of variable
    id_code: str
    """Identifier code of variable.

    This code is used in subsequent value change descriptors
    to map-back to this variable declaration."""

    reference: str
    """Reference name of variable.

    This human-readable name typically corresponds to the name of a
    variable in the model that output the VCD."""

    bit_index: Union[None, int, Tuple[int, int]]
    """Optional range of bits to select from the variable.

    May select a single bit index, e.g. ``ref [ 3 ]``. Or a range of
    bits, e.g. from ``ref [ 7 : 3 ]`` (MSB index then LSB index)."""

    @property
    def ref_str(self) -> str:
        if self.bit_index is None:
            return self.reference
        elif isinstance(self.bit_index, int):
            return f"{self.reference}[{self.bit_index}]"
        else:
            return f"{self.reference}[{self.bit_index[0]}:{self.bit_index[1]}]"


class ScopeDecl(NamedTuple):
    """VCD scope declaration.

    Examples::

       $scope module Foo $end
       $scope
          fork alpha_beta
       $end

    """

    type_: ScopeType  #: Type of scope
    ident: str  #: Scope name


class VectorChange(NamedTuple):
    """Vector value change descriptor.

    A vector value consists of multiple 4-state values, where the four
    states are 0, 1, X, and Z. When a vector value consists entirely
    of 0 and 1 states, :attr:`value` will be an int. Otherwise
    :attr:`value` will be a str.

    """

    id_code: str  #: Identifier code of associated variable.
    value: Union[int, str]  #: New value of associated vector variable.


class RealChange(NamedTuple):
    """Real value (floating point) change descriptor."""

    id_code: str  #: Identifier code of associated variable.
    value: float  #: New value of associated real variable.


class ScalarChange(NamedTuple):
    """Scalar value change descriptor.

    A scalar is a single 4-state value. The value is one of '0', '1',
    'X', or 'Z'.

    """

    id_code: str  #: Identifier code of associated variable.
    value: str  #: New value of associated scalar variable.


class StringChange(NamedTuple):
    """String value change descriptor.

    Strings are VCD extension supported by GTKWave.

    """

    id_code: str  #: Identifier code of associated variable.
    value: str  #: New value of associated string variable.


class Location(NamedTuple):
    """Describe location within VCD stream/file."""

    line: int  #: Line number
    column: int  #: Column number


class Span(NamedTuple):
    """Describe location span within VCD stream/file."""

    start: Location  #: Start of span
    end: Location  #: End of span


class Token(NamedTuple):
    """VCD token yielded from :func:`tokenize()`.

    These are relatively high-level tokens insofar as each token fully
    captures an entire VCD declaration, command, or change descriptor.

    The :attr:`kind` attribute determines the :attr:`data` type. Various
    kind-specific properties provide runtime type-checked access to the
    kind-specific data.

    .. Note::

       The :attr:`data` attribute may be accessed directly to avoid
       runtime type checks and thus achieve better runtime performance
       versus accessing kind-specific properties such as
       :attr:`scalar_change`.

    """

    kind: TokenKind
    "The kind of token."

    span: Span
    "The start and end location of the token within the file/stream."

    data: Union[
        None,  # $enddefinitions $upscope $dump* $end
        int,  # time change
        str,  # $comment, $date, $version
        ScopeDecl,  # $scope
        Timescale,  # $timescale
        VarDecl,  # $var
        ScalarChange,
        VectorChange,
        RealChange,
        StringChange,
    ]
    "Data associated with the token. The data type depends on :attr:`kind`."

    @property
    def comment(self) -> str:
        """Unstructured text from a ``$comment`` declaration."""
        assert self.kind is TokenKind.COMMENT
        assert isinstance(self.data, str)
        return self.data

    @property
    def date(self) -> str:
        """Unstructured text from a ``$date`` declaration."""
        assert self.kind is TokenKind.DATE
        assert isinstance(self.data, str)
        return self.data

    @property
    def scope(self) -> ScopeDecl:
        """Scope type and identifier from ``$scope`` declaration."""
        assert self.kind is TokenKind.SCOPE
        assert isinstance(self.data, ScopeDecl)
        return self.data

    @property
    def timescale(self) -> Timescale:
        """Magnitude and unit from ``$timescale`` declaration."""
        assert self.kind is TokenKind.TIMESCALE
        assert isinstance(self.data, Timescale)
        return self.data

    @property
    def var(self) -> VarDecl:
        """Details from a ``$var`` declaration."""
        assert self.kind is TokenKind.VAR
        assert isinstance(self.data, VarDecl)
        return self.data

    @property
    def version(self) -> str:
        """Unstructured text from a ``$version`` declaration."""
        assert self.kind is TokenKind.VERSION
        assert isinstance(self.data, str)
        return self.data

    @property
    def time_change(self) -> int:
        """Simulation time change."""
        assert self.kind is TokenKind.CHANGE_TIME
        assert isinstance(self.data, int)
        return self.data

    @property
    def scalar_change(self) -> ScalarChange:
        """Scalar value change descriptor."""
        assert self.kind is TokenKind.CHANGE_SCALAR
        assert isinstance(self.data, ScalarChange)
        return self.data

    @property
    def vector_change(self) -> VectorChange:
        """Vector value change descriptor."""
        assert self.kind is TokenKind.CHANGE_VECTOR
        assert isinstance(self.data, VectorChange)
        return self.data

    @property
    def real_change(self) -> RealChange:
        """Real (float) value change descriptor."""
        assert self.kind is TokenKind.CHANGE_REAL
        assert isinstance(self.data, RealChange)
        return self.data

    @property
    def string_change(self) -> StringChange:
        "String value change descriptor."
        assert self.kind is TokenKind.CHANGE_STRING
        assert isinstance(self.data, StringChange)
        return self.data


class VCDParseError(Exception):
    """Catch-all error for any VCD parsing errors."""

    def __init__(self, loc: Location, msg: str) -> None:
        super().__init__(f"{loc.line}:{loc.column}: {msg}")
        self.loc = loc
        "Location within VCD file where error was detected."


HasReadinto = Union[io.BufferedIOBase, io.RawIOBase]


def tokenize(stream: HasReadinto, buf_size: Optional[int] = None) -> Iterator[Token]:
    """Parse VCD stream into tokens.

    The input stream must be opened in binary mode. E.g. with ``open(path, 'rb')``.

    """
    if buf_size is None:
        buf_size = io.DEFAULT_BUFFER_SIZE

    s = _TokenizerState(stream, bytearray(buf_size))

    try:
        while True:
            s.advance()
            yield _parse_token(s)
    except StopIteration:
        return


@dataclass
class _TokenizerState:
    stream: HasReadinto
    buf: bytearray
    pos: int = 0
    end: int = 0
    lineno: int = 1
    column: int = 0

    @property
    def loc(self) -> Location:
        return Location(self.lineno, self.column)

    def span(self, start: Location) -> Span:
        return Span(start, self.loc)

    def advance(self, raise_on_eof: bool = True) -> int:
        if self.pos < self.end:
            self.pos += 1
        else:
            n = self.stream.readinto(self.buf)
            if n:
                self.end = n - 1
                self.pos = 0
            elif raise_on_eof:
                raise StopIteration()
            else:
                return 0
        c = self.buf[self.pos]
        if c == 10:
            self.lineno += 1
            self.column = 1
        else:
            self.column += 1
        return self.buf[self.pos]

    def skip_ws(self) -> int:
        c = self.buf[self.pos]
        while c == 32 or 9 <= c <= 13:
            c = self.advance()
        return c

    def take_ws_after_kw(self, kw: str) -> None:
        if _is_ws(self.buf[self.pos]):
            self.advance()
        else:
            raise VCDParseError(self.loc, f"Expected whitespace after identifier ${kw}")

    def take_decimal(self) -> int:
        digits = []
        c = self.buf[self.pos]
        while 48 <= c <= 57:  # '0' <= c <= '9'
            digits.append(c)
            c = self.advance(raise_on_eof=False)
        if digits:
            return int(bytes(digits))
        else:
            raise VCDParseError(self.loc, "Expected decimal value")

    def take_id_code(self) -> str:
        printables = []
        c = self.buf[self.pos]
        while 33 <= c <= 126:  # printable character
            printables.append(c)
            c = self.advance(raise_on_eof=False)
        if printables:
            return bytes(printables).decode("ascii")
        else:
            raise VCDParseError(self.loc, "Expected id code")

    def take_identifier(self) -> str:
        c = self.buf[self.pos]

        # Simple identifiers must start with letter or underscore
        if (
            65 <= c <= 90  # 'A' <= c <= 'Z'
            or 97 <= c <= 122  # 'a' - 'z'
            or c == 95  # '_'
        ):
            identifier = self.take_simple_identifier()
        elif c == 92:  # '\'
            identifier = self.take_escaped_identifier()
        else:
            raise VCDParseError(self.loc, "Simple identifier must start with a-zA-Z_")

        return bytes(identifier).decode("ascii")

    def take_simple_identifier(self) -> List[int]:
        identifier = [self.buf[self.pos]]
        c = self.advance()

        while (
            48 <= c <= 57  # '0' - '9'
            or 65 <= c <= 90  # 'A' - 'Z'
            or 97 <= c <= 122  # 'a' - 'z'
            or c == 95  # '_'
            or c == 36  # '$'
            or c == 46  # '.' not in spec, but seen in the wild
            or c == 40  # '(' - produced by cva6 core
            or c == 41  # ')' - produced by cva6 core
        ):
            identifier.append(c)
            c = self.advance(raise_on_eof=False)

        return identifier

    def take_escaped_identifier(self) -> List[int]:
        identifier = []
        c = self.advance()
        while c not in (9, 10, 32):  # '\t', '\n', ' '
            if c < 33 or c > 126:  # printable ASCII characters
                raise VCDParseError(
                    self.loc,
                    "Escaped identifier can only contain printable ASCII characters",
                )
            identifier.append(c)
            c = self.advance()

        return identifier

    def take_bit_index(self) -> Union[int, Tuple[int, int]]:
        self.skip_ws()
        index0 = self.take_decimal()
        index1: Optional[int]

        c = self.skip_ws()
        if c == 58:  # ':'
            self.advance()
            self.skip_ws()
            index1 = self.take_decimal()
        else:
            index1 = None

        c = self.skip_ws()
        if c == 93:  # ']'
            self.advance(raise_on_eof=False)
            if index1 is None:
                return index0
            else:
                return (index0, index1)
        else:
            raise VCDParseError(self.loc, 'Expected bit index to terminate with "]"')

    def take_to_end(self) -> str:
        chars = [
            self.buf[self.pos],  # $
            self.advance(),  # --> e
            self.advance(),  # --> n
            self.advance(),  # --> d
        ]
        while not (  # Check for 'd' 'n' 'e' '$'
            chars[-1] == 100
            and chars[-2] == 110
            and chars[-3] == 101
            and chars[-4] == 36
        ):
            chars.append(self.advance())

        if len(chars) > 4 and not _is_ws(chars[-5]):
            loc = Location(self.lineno, self.column - min(len(chars), 5))
            raise VCDParseError(loc, "Expected whitespace before $end")

        return bytes(chars[:-5]).decode("ascii")

    def take_end(self) -> None:
        if (
            self.skip_ws() != 36  # '$'
            or self.advance() != 101  # 'e'
            or self.advance() != 110  # 'n'
            or self.advance() != 100  # 'd'
        ):
            raise VCDParseError(self.loc, "Expected $end")


def _is_ws(c: int) -> bool:
    return c == 32 or 9 <= c <= 13


def _parse_token(s: _TokenizerState) -> Token:
    c = s.skip_ws()
    start = s.loc
    if c == 35:  # '#'
        # Parse time change
        s.advance()
        time = s.take_decimal()
        return Token(TokenKind.CHANGE_TIME, s.span(start), time)
    elif c == 48 or c == 49 or c == 122 or c == 90 or c == 120 or c == 88:
        # c in '01zZxX'
        # Parse scalar change
        scalar_value = chr(c)
        s.advance()
        id_code = s.take_id_code()
        return Token(
            TokenKind.CHANGE_SCALAR, s.span(start), ScalarChange(id_code, scalar_value)
        )
    elif c == 66 or c == 98:  # 'B' or 'b'
        # Parse vector change
        vector = []
        c = s.advance()
        while c == 48 or c == 49:  # '0' or '1'
            vector.append(c)
            c = s.advance()
        vector_value: Union[int, str]

        if c == 122 or c == 90 or c == 120 or c == 88:  # c in 'zZxX'
            vector.append(c)
            c = s.advance()
            while (
                c == 48 or c == 49 or c == 122 or c == 90 or c == 120 or c == 88
            ):  # c in '01zZxX'
                vector.append(c)
                c = s.advance()
            vector_value = bytes(vector).decode("ascii")
        else:
            vector_value = int(bytes(vector), 2)

        if not _is_ws(c):
            raise VCDParseError(s.loc, "Expected whitespace after vector value")

        s.skip_ws()

        id_code = s.take_id_code()

        return Token(
            TokenKind.CHANGE_VECTOR, s.span(start), VectorChange(id_code, vector_value)
        )
    elif c == 82 or c == 114:  # 'R' or 'r'
        # Parse real change
        real_digits = []
        c = s.advance()

        while not _is_ws(c):
            real_digits.append(c)
            c = s.advance()

        try:
            real = float(bytes(real_digits))
        except ValueError:
            real_str = bytes(real_digits).decode("ascii")
            raise VCDParseError(
                start, f"Expected real value, got: {real_str}"
            ) from None

        s.skip_ws()

        id_code = s.take_id_code()

        return Token(TokenKind.CHANGE_REAL, s.span(start), RealChange(id_code, real))
    elif c == 83 or c == 115:  # 'S' or 's'
        chars = []
        c = s.advance()
        while not _is_ws(c):
            chars.append(c)
            c = s.advance()
        s.skip_ws()
        id_code = s.take_id_code()
        string_value = bytes(chars).decode("ascii")
        return Token(
            TokenKind.CHANGE_STRING, s.span(start), StringChange(id_code, string_value)
        )
    elif c == 36:  # '$'
        s.advance()
        kw = s.take_identifier()

        if kw == "comment":
            s.take_ws_after_kw(kw)
            comment = s.take_to_end()
            return Token(TokenKind.COMMENT, s.span(start), comment)
        elif kw == "date":
            s.take_ws_after_kw(kw)
            date_str = s.take_to_end()
            return Token(TokenKind.DATE, s.span(start), date_str)
        elif kw == "enddefinitions":
            s.take_ws_after_kw(kw)
            s.take_end()
            return Token(TokenKind.ENDDEFINITIONS, s.span(start), None)
        elif kw == "scope":
            s.take_ws_after_kw(kw)
            s.skip_ws()
            identifier = s.take_identifier()
            try:
                scope_type = ScopeType(identifier)
            except ValueError:
                raise VCDParseError(
                    s.loc, f"Invalid $scope type: {identifier}"
                ) from None

            s.skip_ws()

            scope_ident = s.take_identifier()

            s.take_end()

            scope_decl = ScopeDecl(scope_type, scope_ident)

            return Token(TokenKind.SCOPE, s.span(start), scope_decl)
        elif kw == "timescale":
            s.take_ws_after_kw(kw)
            s.skip_ws()
            mag_int = s.take_decimal()

            try:
                magnitude = TimescaleMagnitude(mag_int)
            except ValueError:
                valid_magnitudes = ", ".join(str(m.value) for m in TimescaleMagnitude)
                raise VCDParseError(
                    s.loc,
                    f"Invalid $timescale magnitude: {mag_int}. "
                    f"Must be one of: {valid_magnitudes}.",
                ) from None

            s.skip_ws()
            unit_str = s.take_identifier()
            try:
                unit = TimescaleUnit(unit_str)
            except ValueError:
                valid_units = ", ".join(u.value for u in TimescaleUnit)
                raise VCDParseError(
                    s.loc,
                    f"Invalid $timescale unit: {unit_str}. "
                    f"Must be one of: {valid_units}.",
                ) from None

            s.take_end()

            timescale = Timescale(magnitude, unit)
            return Token(TokenKind.TIMESCALE, s.span(start), timescale)
        elif kw == "upscope":
            s.take_ws_after_kw(kw)
            s.take_end()
            return Token(TokenKind.UPSCOPE, s.span(start), None)
        elif kw == "var":
            s.take_ws_after_kw(kw)
            s.skip_ws()
            type_str = s.take_identifier()
            try:
                type_ = VarType(type_str)
            except ValueError:
                valid_types = ", ".join(t.value for t in VarType)
                raise VCDParseError(
                    s.loc,
                    f"Invalid $var type: {type_str}. Must be one of: {valid_types}",
                ) from None

            s.skip_ws()
            size = s.take_decimal()
            s.skip_ws()
            id_code = s.take_id_code()
            s.skip_ws()
            ident = s.take_identifier()

            bit_index: Union[None, int, Tuple[int, int]]
            c = s.skip_ws()
            if c == 91:  # '['
                s.advance()
                bit_index = s.take_bit_index()
            else:
                bit_index = None

            s.take_end()
            var_decl = VarDecl(type_, size, id_code, ident, bit_index)
            return Token(TokenKind.VAR, s.span(start), var_decl)
        elif kw == "version":
            s.take_ws_after_kw(kw)
            version = s.take_to_end()
            return Token(TokenKind.VERSION, s.span(start), version)
        elif kw == "dumpall":
            return Token(TokenKind.DUMPALL, s.span(start), None)
        elif kw == "dumpoff":
            return Token(TokenKind.DUMPOFF, s.span(start), None)
        elif kw == "dumpon":
            return Token(TokenKind.DUMPON, s.span(start), None)
        elif kw == "dumpvars":
            return Token(TokenKind.DUMPVARS, s.span(start), None)
        elif kw == "end":
            return Token(TokenKind.END, s.span(start), None)
        else:
            raise VCDParseError(s.loc, f"invalid keyword ${kw}")
    else:
        raise VCDParseError(s.loc, f"confused: {chr(c)}")
