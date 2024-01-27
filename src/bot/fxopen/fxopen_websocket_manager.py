import base64
from datetime import datetime, timezone
import hmac
import hashlib
import json
from config.config_service import ConfigService


class FxOpenWebsocketManager:
    configService = ConfigService()

    def send_auth_message(self, ws, websocket_id: str):
        print('sending auth message')

        timestamp = round(datetime.now(tz=timezone.utc).timestamp() * 1000)
        signature = f'{timestamp}{self.configService.get_web_api_id()}{self.configService.get_web_api_key()}'
        base64HmacSignature = base64.b64encode(hmac.new(
            key=self.configService.get_web_api_secret().encode(),
            msg=signature.encode(),
            digestmod=hashlib.sha256
        ).digest()).decode()

        ws.send(json.dumps({
            "Id": websocket_id,
            "Request": "Login",
            "Params": {
                "AuthType": "HMAC",
                "WebApiId":  self.configService.get_web_api_id(),
                "WebApiKey": self.configService.get_web_api_key(),
                "Timestamp": timestamp,
                "Signature": base64HmacSignature,
                "DeviceId":  "123",
                "AppSessionId":  "123"
            }
        }))
