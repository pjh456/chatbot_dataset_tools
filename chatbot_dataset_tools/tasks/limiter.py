import time
import threading


class TokenBucketLimiter:
    """
    线程安全的令牌桶限流器。
    允许高并发获取令牌，并在锁外进行睡眠等待。
    """

    def __init__(self, rate: float):
        self.rate = rate
        self.enabled = rate > 0
        self._tokens = 1.0  # 初始令牌数 (允许一定的突发)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def wait(self):
        """
        计算并执行等待。
        该方法是阻塞的，但 'sleep' 发生在锁外，不会阻塞其他线程获取令牌。
        """
        if not self.enabled:
            return

        wait_time = 0.0

        with self._lock:
            now = time.monotonic()
            # 1. 补充令牌 (根据时间差)
            elapsed = now - self._last_update
            self._last_update = now
            self._tokens = min(1.0, self._tokens + elapsed * self.rate)

            # 2. 尝试获取令牌
            if self._tokens >= 1.0:
                # 令牌充足，消耗一个，无需等待
                self._tokens -= 1.0
            else:
                # 令牌不足，计算需要等待多久才能攒够 1.0 个令牌
                deficit = 1.0 - self._tokens
                wait_time = deficit / self.rate

                # 在这里 "预支" 了未来的令牌，
                # 这样其他线程进来时，会计算出更长的等待时间，从而实现排队。
                self._tokens -= 1.0  # 变成负数，代表负债

        # 3. 在锁外睡眠 (真正的并发关键)
        if wait_time > 0:
            time.sleep(wait_time)
