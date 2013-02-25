# -*- coding: UTF-8 -*-


class BaseAction(object):
    name = "base action"

    def op(self, model):
        return ""

    def success_message(self, model):
        return ""

    def error_message(self, model):
        return ""

    def enabled(self, model):
        return True

    def disabled_tooltip(self, model):
        return ""