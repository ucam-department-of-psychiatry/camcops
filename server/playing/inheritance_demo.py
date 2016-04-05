#!/usr/bin/env python3


class Base(object):  # make it a new-style class by inheriting from object
    print("Base")
    sx = 5

    @classmethod
    def cm(cls):
        print("classmethod: base")

    def __init__(self):
        print("Base.__init__")
        self.x = 6

    def foo(self):
        print("Base foo, self.x = {}, Base.sx = {}".format(self.x, Base.sx))
        print("Calling self.bar() from Base.foo():")
        self.bar()

    def bar(self):
        print("Base bar")


class Derived(Base):
    print("Derived")
    sx = 10

    @classmethod
    def cm(cls):
        print("classmethod: derived")

    def __init__(self):
        print("Derived.__init__")
        self.x = 15

    def foo(self):
        print("Derived foo, self.x = {}, Derived.sx = {}".format(self.x,
                                                                 Derived.sx))
        print("Calling self.bar() from Derived.foo():")
        self.bar()
        print("Calling super.foo() from Derived.foo():")
        super(Derived, self).foo()

    def bar(self):
        print("Derived bar")


print("Making b (Base)")
b = Base()
print("Calling b.foo()")
b.foo()
print("Calling b.cm()")
b.cm()

print("Making d (Derived)")
d = Derived()
print("Calling d.foo()")
d.foo()
print("Calling d.cm()")
d.cm()

for cls in Base.__subclasses__():
    cls.cm()


class B1(object):
    def foo(self):
        print("B1.foo")


class B2(object):
    def foo(self):
        print("B2.foo")


class D(B1, B2):
    def foo(self):
        # http://python-history.blogspot.co.uk/2010/06/method-resolution-order.html
        print("D.foo; calling super().foo()")
        super().foo()

x = D()
x.foo()

