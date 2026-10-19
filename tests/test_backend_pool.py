from ufaflow.server import Backend, BackendPool


def test_round_robin_simple():
    b1 = Backend("127.0.0.1", 8001)
    b2 = Backend("127.0.0.1", 8002)
    pool = BackendPool([b1, b2], algorithm="round_robin")
    seq = [pool.choose().name for _ in range(4)]
    assert seq[0] != seq[1]
    assert len(set(seq)) == 2


def test_least_conn():
    b1 = Backend("127.0.0.1", 8001)
    b2 = Backend("127.0.0.1", 8002)
    b2.current_conns = 5
    pool = BackendPool([b1, b2], algorithm="least_conn")
    chosen = pool.choose()
    assert chosen is b1
