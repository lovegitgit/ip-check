#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class CommonConfig:

    def __str__(self) -> str:
        variables = vars(self)
        info = '#############################\n'
        for k, v in variables.items():
            temp_str = f"{k} = {v}\n"
            type_of_v = type(v)
            if type_of_v == str:
                temp_str = f"{k} = '{v}'\n"
            info += temp_str
        info += '#############################'
        return info