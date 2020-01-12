from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from api.restricter_pb2_grpc import add_RestrictServicer_to_server, RestrictServicer
from api.restricter_pb2 import DESCRIPTOR, Restricted, RestrictRequest, IDsRequest, IDs


class Restricter(RestrictServicer):
    def restrict(self, request: RestrictRequest, context: grpc.ServicerContext):
        out = {}
        for key in request.keys:
            out[key] = "some value"
        return Restricted(data=out)

    def ids(self, request: IDsRequest, context: grpc.ServicerContext):
        return IDs(ids=[1, 2, 3])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_RestrictServicer_to_server(Restricter(), server)
    service_names = (
        DESCRIPTOR.services_by_name['Restrict'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)
    server.add_insecure_port('[::]:9002')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()