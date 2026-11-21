import base64
import json
import sys
from pathlib import Path

from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh

app = create_app(CauHinh(duong_dan_csdl=sys.argv[1], khoa_bi_mat="temporary-browser-test-secret"))
result = app.test_cli_runner().invoke(args=[
    "seed", "--mat-khau-kho", "test-only-pass", "--mat-khau-ban-hang", "test-only-pass",
])
assert result.exit_code == 0, (result.output, repr(result.exception))
client = app.test_client(use_cookies=False)
for line in sys.stdin:
    req = json.loads(line)
    response = client.open(req["path"], method=req["method"], headers=req["headers"],
                           data=base64.b64decode(req["body"]))
    print(json.dumps({"id": req["id"], "status": response.status_code,
                     "headers": dict(response.headers),
                     "body": base64.b64encode(response.data).decode()}), flush=True)
