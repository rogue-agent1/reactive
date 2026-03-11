#!/usr/bin/env python3
"""reactive — Reactive programming with observables, operators, schedulers. Zero deps."""

class Observable:
    def __init__(self, subscribe_fn=None):
        self._subscribe = subscribe_fn

    def subscribe(self, on_next=None, on_error=None, on_complete=None):
        observer = Observer(on_next, on_error, on_complete)
        if self._subscribe: self._subscribe(observer)
        return observer

    @staticmethod
    def of(*values):
        def sub(obs):
            for v in values: obs.next(v)
            obs.complete()
        return Observable(sub)

    @staticmethod
    def range(start, count):
        return Observable.of(*range(start, start + count))

    def map(self, fn):
        src = self
        def sub(obs):
            src.subscribe(lambda v: obs.next(fn(v)), obs.error, obs.complete)
        return Observable(sub)

    def filter(self, pred):
        src = self
        def sub(obs):
            src.subscribe(lambda v: obs.next(v) if pred(v) else None, obs.error, obs.complete)
        return Observable(sub)

    def reduce(self, fn, seed):
        src = self
        def sub(obs):
            acc = [seed]
            def on_next(v): acc[0] = fn(acc[0], v)
            def on_complete(): obs.next(acc[0]); obs.complete()
            src.subscribe(on_next, obs.error, on_complete)
        return Observable(sub)

    def take(self, n):
        src = self
        def sub(obs):
            count = [0]
            def on_next(v):
                if count[0] < n: obs.next(v); count[0] += 1
                if count[0] >= n: obs.complete()
            src.subscribe(on_next, obs.error, obs.complete)
        return Observable(sub)

    def scan(self, fn, seed):
        src = self
        def sub(obs):
            acc = [seed]
            def on_next(v): acc[0] = fn(acc[0], v); obs.next(acc[0])
            src.subscribe(on_next, obs.error, obs.complete)
        return Observable(sub)

    def flat_map(self, fn):
        src = self
        def sub(obs):
            def on_next(v):
                inner = fn(v)
                inner.subscribe(obs.next, obs.error)
            src.subscribe(on_next, obs.error, obs.complete)
        return Observable(sub)

class Observer:
    def __init__(self, on_next=None, on_error=None, on_complete=None):
        self._next = on_next or (lambda v: None)
        self._error = on_error or (lambda e: None)
        self._complete = on_complete or (lambda: None)
        self.closed = False

    def next(self, value):
        if not self.closed: self._next(value)
    def error(self, err):
        if not self.closed: self._error(err); self.closed = True
    def complete(self):
        if not self.closed: self._complete(); self.closed = True

class Subject(Observable):
    def __init__(self):
        self.observers = []
        super().__init__(lambda obs: self.observers.append(obs))

    def next(self, value):
        for obs in self.observers: obs.next(value)
    def complete(self):
        for obs in self.observers: obs.complete()

def main():
    print("Reactive Programming:\n")
    results = []
    Observable.range(1, 10).filter(lambda x: x % 2 == 0).map(lambda x: x ** 2).subscribe(
        on_next=lambda v: results.append(v))
    print(f"  range(1,10).filter(even).map(x²): {results}")

    Observable.of(1,2,3,4,5).scan(lambda a,b: a+b, 0).subscribe(
        on_next=lambda v: print(f"    running sum: {v}"))

    Observable.of(3,1,4,1,5).reduce(lambda a,b: a+b, 0).subscribe(
        on_next=lambda v: print(f"  reduce(sum): {v}"))

    sub = Subject()
    sub.map(lambda x: x.upper()).subscribe(on_next=lambda v: print(f"  subject: {v}"))
    sub.next("hello"); sub.next("world"); sub.complete()

if __name__ == "__main__":
    main()
