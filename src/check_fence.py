from generator import _strip_json_fence

fenced = "```json\n{\"a\": 1}\n```"
plain = "{\"a\": 2}"

print("fenced →", repr(_strip_json_fence(fenced)))
print("plain  →", repr(_strip_json_fence(plain)))

import json
print("parse fenced:", json.loads(_strip_json_fence(fenced)))
print("parse plain :", json.loads(_strip_json_fence(plain)))