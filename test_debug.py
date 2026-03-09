
import unittest
from unittest.mock import patch
import os

class TestDebug(unittest.TestCase):
    def test_patch_exists(self):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            print(f"Before call: {mock_exists.call_count}")
            res = os.path.exists("something")
            print(f"After call: {mock_exists.call_count}")
            print(f"Result: {res}")

if __name__ == "__main__":
    unittest.main()
