from unittest import TestCase
from error.reporter import SourceCodeMaker
from dis import dis

class TestLineMarker(TestCase):


    def test_line_marker(self):
        s = """
        let a = 1;
        let 123;
        let b = 1;
        let c;
        """
        marker = SourceCodeMaker(s)
        msg =  marker.mark((2, 5), (2, 7), context=(1, 4))
        print(msg)

        # msg = marker.mark((3, 3), (5, 3))
        # print(msg)