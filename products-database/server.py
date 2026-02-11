from concurrent import futures
import logging

import grpc
import products_pb2
import products_pb2_grpc


class Greeter(products_pb2_grpc.SellerService):
    def CreateAccount(self, request, context):
        return products_pb2.CreateAccountResponse()

    def Login(self, request, context):
        return products_pb2.LoginResponse()

    def Logout(self, request, context):
        return products_pb2.LogoutResponse()

    def GetSellerRating(self, request, context):
        return products_pb2.RatingResponse()

    def RegisterItemForSale(self, request, context):
        return products_pb2.RegisterItemResponse()

    def ChangeItemPrice(self, request, context):
        return products_pb2.ChangeItemPriceResponse()

    def UpdateUnitsForSale(self, request, context):
        return products_pb2.UpdateUnitsResponse()

    def DisplayItemsForSale(self, request, context):
        return products_pb2.ItemListResponse()

    def GetCategories(self, request, context):
        return products_pb2.CategoryListResponse()


def serve():
    port = "5000"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    products_pb2_grpc.add_SellerServiceServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
