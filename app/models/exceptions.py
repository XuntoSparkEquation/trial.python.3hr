from typing import List


class InvalidUsage(Exception):
    msg: str
    code: int

    def __init__(self, msg: str, code: 404):
        super(InvalidUsage, self).__init__()
        self.msg = msg
        self.code = code


class NotFound(InvalidUsage):
    def __init__(self, resources: List[str]):
        super(NotFound, self).__init__(f"Resources are not found: {resources}", 404)
