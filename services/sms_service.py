import requests

from flask import current_app


class BMSSMSService:

    def __init__(self):

        self.api_key = current_app.config.get(
            "BMS_API_KEY",
            ""
        )

        self.sender_id = current_app.config.get(
            "BMS_SENDER_ID",
            ""
        )

        self.enabled = current_app.config.get(
            "BMS_ENABLED",
            False
        )


    def is_configured(self):

        return bool(
            self.api_key
            and self.sender_id
        )


    def test_configuration(self):

        if not self.api_key:

            return {
                "success": False,
                "message": (
                    "BMS API key is not configured."
                )
            }

        if not self.sender_id:

            return {
                "success": False,
                "message": (
                    "BMS sender ID is not configured."
                )
            }

        return {
            "success": True,
            "message": (
                "BMS configuration is present."
            )
        }


    def send_test_sms(
        self,
        phone,
        message
    ):

        if not self.enabled:

            return {
                "success": False,
                "status": "disabled",
                "message": (
                    "BMS SMS sending is disabled."
                )
            }


        if not self.is_configured():

            return {
                "success": False,
                "status": "not_configured",
                "message": (
                    "BMS is not configured."
                )
            }


        phone = phone.strip()


        if not phone:

            return {
                "success": False,
                "status": "invalid_phone",
                "message": (
                    "Test phone number is required."
                )
            }


        if not message.strip():

            return {
                "success": False,
                "status": "empty_message",
                "message": (
                    "Test message cannot be empty."
                )
            }


        try:

            response = requests.post(
                "https://api.mnotify.com/api/sms/quick",
                params={
                    "key": self.api_key
                },
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "recipient": [phone],
                    "sender": self.sender_id,
                    "message": message,
                    "is_schedule": False,
                    "schedule_date": ""
                },
                timeout=30
            )


            try:

                data = response.json()

            except ValueError:

                data = {
                    "raw_response": response.text
                }


            if (
                response.ok
                and (
                    data.get("status") == "success"
                    or data.get("code") == 2000
                )
            ):

                return {
                    "success": True,
                    "status": "sent",
                    "message": (
                        "Test SMS submitted successfully."
                    ),
                    "response": data
                }


            return {
                "success": False,
                "status": "failed",
                "message": data.get(
                    "message",
                    (
                        "BMS returned HTTP "
                        f"{response.status_code}."
                    )
                ),
                "response": data
            }


        except requests.RequestException as exc:

            return {
                "success": False,
                "status": "connection_error",
                "message": (
                    f"Could not connect to BMS: {exc}"
                )
            }


    def send_sms(
        self,
        recipients,
        message
    ):

        if not self.enabled:

            return {
                "success": False,
                "status": "disabled",
                "message": (
                    "BMS SMS sending is currently disabled."
                )
            }


        if not self.is_configured():

            return {
                "success": False,
                "status": "not_configured",
                "message": (
                    "BMS SMS gateway is not configured."
                )
            }


        if not recipients:

            return {
                "success": False,
                "status": "no_recipients",
                "message": (
                    "No SMS recipients were provided."
                )
            }


        if not message:

            return {
                "success": False,
                "status": "empty_message",
                "message": (
                    "SMS message cannot be empty."
                )
            }


        try:

            response = requests.post(
                "https://api.mnotify.com/api/sms/quick",
                params={
                    "key": self.api_key
                },
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "recipient": recipients,
                    "sender": self.sender_id,
                    "message": message,
                    "is_schedule": False,
                    "schedule_date": ""
                },
                timeout=30
            )


            try:

                data = response.json()

            except ValueError:

                data = {
                    "raw_response": response.text
                }


            if (
                response.ok
                and (
                    data.get("status") == "success"
                    or data.get("code") == 2000
                )
            ):

                return {
                    "success": True,
                    "status": "sent",
                    "message": (
                        "SMS submitted successfully."
                    ),
                    "response": data
                }


            return {
                "success": False,
                "status": "failed",
                "message": data.get(
                    "message",
                    "BMS rejected the SMS request."
                ),
                "response": data
            }


        except requests.RequestException as exc:

            return {
                "success": False,
                "status": "failed",
                "message": (
                    f"Could not connect to BMS: {exc}"
                )
            }