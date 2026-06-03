from locust import HttpUser, task, constant
from bs4 import BeautifulSoup
from itertools import cycle
import logging

# =========================================================
# ENDPOINTS BENIGNOS DVWA
# =========================================================

ENDPOINTS = [
    # SQLi GET
    {
        "method": "GET",
        "path": "/vulnerabilities/sqli/?id={{payload}}&Submit=Submit",
        "payload": "1"
    },

    # SQLi POST
    {
        "method": "POST",
        "path": "/vulnerabilities/sqli/",
        "body": "id={{payload}}&Submit=Submit",
        "payload": "2"
    },

    # Command Injection GET
    {
        "method": "GET",
        "path": "/vulnerabilities/exec/?ip={{payload}}&Submit=Submit",
        "payload": "127.0.0.1"
    },

    # Command Injection POST
    {
        "method": "POST",
        "path": "/vulnerabilities/exec/",
        "body": "ip={{payload}}&Submit=Submit",
        "payload": "8.8.8.8"
    },

    # Blind SQLi
    {
        "method": "GET",
        "path": "/vulnerabilities/sqli_blind/?id={{payload}}&Submit=Submit",
        "payload": "3"
    },

    # File Inclusion
    {
        "method": "GET",
        "path": "/vulnerabilities/fi/?page={{payload}}",
        "payload": "include.php"
    },

    # Reflected XSS
    {
        "method": "GET",
        "path": "/vulnerabilities/xss_r/?name={{payload}}",
        "payload": "Juan"
    },


    {
        "method": "POST",
        "path": "/vulnerabilities/xss_s/",
        "body": (
            "txtName={{payload}}&"
            "mtxMessage={{payload}}&"
            "btnSign=Sign"
        ),
        "payload": "Usuario"
    }
]

# =========================================================
# ROUND ROBIN
# =========================================================

endpoint_cycler = cycle(ENDPOINTS)

# =========================================================
# LOCUST USER
# =========================================================

class DVWALoadUser(HttpUser):

    wait_time = constant(2)

    host = "http://100.118.62.112:8090"

    # -----------------------------------------------------
    # LOGIN + SECURITY LOW
    # -----------------------------------------------------

    def on_start(self):

        # =========================
        # LOGIN PAGE
        # =========================

        response = self.client.get("/login.php")

        print("STATUS:", response.status_code)
        print("URL:", response.url)
        print(response.text[:1000])

        soup = BeautifulSoup(response.text, "html.parser")

        user_token = soup.find(
            "input",
            {"name": "user_token"}
        )["value"]

        # =========================
        # LOGIN
        # =========================

        login_data = {
            "username": "admin",
            "password": "password",
            "Login": "Login",
            "user_token": user_token
        }

        with self.client.post(
            "/login.php",
            data=login_data,
            allow_redirects=True,
            catch_response=True
        ) as response:

            if "login.php" in response.url.lower():
                response.failure("Login fallido")
                raise Exception("Login fallido")

            response.success()

        # =========================
        # CONFIG SECURITY LOW
        # =========================

        security_page = self.client.get("/security.php")

        soup = BeautifulSoup(
            security_page.text,
            "html.parser"
        )

        security_token = soup.find(
            "input",
            {"name": "user_token"}
        )["value"]

        security_data = {
            "security": "low",
            "seclev_submit": "Submit",
            "user_token": security_token
        }

        self.client.post(
            "/security.php",
            data=security_data
        )

        logging.info("Seguridad configurada en LOW")

        # =========================
        # ASIGNAR ENDPOINT
        # =========================

        self.endpoint = next(endpoint_cycler)

        self.payload = self.endpoint.get("payload", "")

        logging.info(
            f"Usuario asignado a endpoint: "
            f"{self.endpoint['path']}"
        )

    # -----------------------------------------------------
    # TASK
    # -----------------------------------------------------

    @task
    def hacer_peticion(self):

        method = self.endpoint["method"].upper()

        # =========================
        # GET
        # =========================

        if method == "GET":

            path = self.endpoint["path"].replace(
                "{{payload}}",
                self.payload
            )

            self.client.get(
                path,
                name=self.endpoint["path"]
            )

        # =========================
        # POST
        # =========================

        elif method == "POST":

            path = self.endpoint["path"]

            # XSS Stored
            if "xss_s" in path:

                data = {
                    "txtName": self.payload,
                    "mtxMessage": f"Hola {self.payload}",
                    "btnSign": "Sign"
                }

            # Otros POST
            else:

                raw_body = self.endpoint.get(
                    "body",
                    ""
                ).replace(
                    "{{payload}}",
                    self.payload
                )

                # Convertir body a dict
                data = dict(
                    item.split("=")
                    for item in raw_body.split("&")
                )

            with self.client.post(
                path,
                data=data,
                catch_response=True,
                name=self.endpoint["path"]
            ) as response:


                if "login.php" in response.text:
                    response.failure("Redirected to login")