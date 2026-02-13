import logging
import random

logging.basicConfig(level=logging.ERROR)

from spyne import Application, rpc, ServiceBase, Float, Unicode

from spyne import Iterable

from spyne.protocol.soap import Soap11
from spyne.protocol.json import JsonDocument

from spyne.server.wsgi import WsgiApplication


class PaymentsService(ServiceBase):
    @rpc(Unicode, Unicode, Unicode, Unicode, Float, _returns=Unicode)
    def pay(ctx, name, card_number, expiration_date, security_code, amount):

        # 90% chance of "Yes", 10% chance of "No"
        result = "Yes" if random.random() < 0.9 else "No"
        return result


application = Application(
    [PaymentsService],
    tns="distmark.transactions.payments",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

if __name__ == "__main__":
    # You can use any Wsgi server. Here, we chose
    # Python's built-in wsgi server but you're not
    # supposed to use it in production.
    from wsgiref.simple_server import make_server

    wsgi_app = WsgiApplication(application)
    server = make_server("0.0.0.0", 5000, wsgi_app)
    print("Soap Server running on http://0.0.0.0:5000")
    print("WSDL at http://0.0.0.0:5000/?wsdl")
    server.serve_forever()
