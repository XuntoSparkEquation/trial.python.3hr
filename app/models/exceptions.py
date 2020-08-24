from typing import List


class InvalidUsage(Exception):
    msg: str
    code: int

    def __init__(self, msg: str, code: int):
        super(InvalidUsage, self).__init__()
        self.msg = msg
        self.code = code

    def errors(self):
        return [{"msg": self.msg, "type": "invalid_usage"}]


class NotFound(InvalidUsage):
    def __init__(self, resources: List[str]):
        super(NotFound, self).__init__(f"Resources are not found: {resources}", 404)
