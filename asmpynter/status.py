# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#

import textwrap


class StatusView(object):

    def __init__(self):
        pass


class RegStatusView(StatusView):

    def __init__(self, rename_map, blacklist_map, flag_register, flag_names, bnum):
        self.rename_map = rename_map
        self.blacklist_map = blacklist_map
        self.flag_register = flag_register
        self.flag_names = flag_names
        self.bnum = bnum
        if flag_register in self.rename_map:
            self.flag_reg_name = self.rename_map[flag_register]
        else:
            self.flag_reg_name = flag_register

    def view(self, reg_map):
        els = []
        keys = sorted(reg_map, key=lambda e: e.upper())
        for k in keys:
            if k in self.blacklist_map:
                continue
            if k == self.flag_register:
                continue
            if k in self.rename_map:
                name = self.rename_map[k]
            else:
                name = k
            els.append(self._reg_to_str(name, reg_map[k]))
        st = ''

        # TODO: implement something better!
        s = 4
        if self.bnum > 4:
            s = 3

        finalels = [' '.join(els[n:n+s]) for n in range(0, len(els), s)]
        if self.flag_register in reg_map:
            finalels.append(self._flags_to_str(self.flag_reg_name,
                                               reg_map[self.flag_register]
                                               ))

        return '\n'.join(finalels)

    def _reg_to_str(self, name, value):
        form = '{{:3s}}: {{:#0{0}x}}'.format(self.bnum * 2 + 2)
        return form.format(name.upper(), value)

    def _flags_to_str(self, name, value):
        i = 0x1
        res = []
        for n in self.flag_names:
            if n != '_' and i & value != 0:
                res.append(n)
            i = i << 1
        return '%s: %s' % (name.upper(), ' '.join(res))
