from socket import MSG_PEEK

from gunicorn.workers.gthread import TConn, ThreadWorker


class OpenSlidesThreadWorker(ThreadWorker):
    def enqueue_req(self, conn: TConn) -> None:
        # Peek into the sockets content to be able to read out the path part of the header (which ought to be the part after the first whitespace).
        peek = str(conn.sock.recv(4096, MSG_PEEK)).split()

        if len(peek) >= 2 and "system/action/health" in peek[1]:
            # If the health route is recognized, set data_ready to True to stop handle from returning _DEFER and force it into working instead.
            # Since the message could be read, the data is probably there already,
            # the health route doesn't take a payload to begin with.
            conn.data_ready = True
            # Call the base class methods used in the base method in order, don't enthread them.
            res = self.handle(conn)
            self.finish_request(conn, res)
        else:
            super().enqueue_req(conn)
