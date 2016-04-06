import six
import pytest


@pytest.yield_fixture
def gtkw():
    import vcd.gtkw
    sio = six.StringIO()
    gtkw = vcd.gtkw.GTKWSave(sio)
    try:
        yield gtkw
    finally:
        sio.close()
