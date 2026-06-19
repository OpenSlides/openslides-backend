from socket import MSG_PEEK

from gunicorn.workers.gthread import TConn, ThreadWorker


class OpenSlidesThreadWorker(ThreadWorker):
    def enqueue_req(self, conn: TConn) -> None:
        peek = str(conn.sock.recv(4096, MSG_PEEK)).split()
        if len(peek) >= 2 and "system/action/health" in peek[1]:
            conn.data_ready = True
            res = self.handle(conn)
            self.finish_request(conn, res)
        else:
            super().enqueue_req(conn)
