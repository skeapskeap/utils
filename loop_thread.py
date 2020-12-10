import threading
import time

class LoopRun():

    def __init__(self, func=object, interval=1):
        self.func = func
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            self.func()
            time.sleep(self.interval)


def counter(func):
    c = 0
    def wrapper(*args):
        nonlocal c
        c += 1
        return func(c)
    return wrapper


@counter
def my_func(*args):
    print(f'run func at {args[0]} time; ', end='')
    print(f'active threads = {threading.active_count()}')


LoopRun(my_func, 3)

while True:
    try:
        pass
    except KeyboardInterrupt:
        break
