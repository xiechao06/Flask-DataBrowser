# -*- coding: utf-8 -*-


class Kolumne(object):
    def is_relationship(self):
        raise NotImplementedError

    @property
    def key(self):
        raise NotImplementedError

    @property
    def direction(self):
        raise NotImplementedError

    @property
    def remote_side(self):
        raise NotImplementedError

    def make_field(self, col_spec):
        raise NotImplementedError

    @property
    def doc(self):
        raise NotImplementedError