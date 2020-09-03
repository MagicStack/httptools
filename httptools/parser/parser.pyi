from typing import Optional

class URL:
	def __init__(self):
		self.schema: Optional[bytes] = None
		self.host: Optional[bytes] = None
		self.port: Optional[int] = None
		self.query: Optional[bytes] = None
		self.fragment: Optional[bytes] = None
		self.userinfo: Optional[bytes] = None
