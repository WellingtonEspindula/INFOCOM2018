def rename_switch(switch_name: str) -> str:
    ran_lower_bound = 1
    ran_upper_bound = 20

    metro_lower_bound = 21
    metro_upper_bound = 25

    access_lower_bound = 26
    access_upper_bound = 29

    core_lower_bound = 30
    core_upper_bound = 33

    internet_lower_bound = 34
    internet_upper_bound = 34

    sp = int(switch_name[1:])
    if ran_lower_bound <= sp <= ran_upper_bound:
        return create_switch_name(sp, ran_lower_bound, 'r')
    elif metro_lower_bound <= sp <= metro_upper_bound:
        return create_switch_name(sp, metro_lower_bound, 'm')
    elif access_lower_bound <= sp <= access_upper_bound:
        return create_switch_name(sp, access_lower_bound, 'a')
    elif core_lower_bound <= sp <= core_upper_bound:
        return create_switch_name(sp, core_lower_bound, 'c')
    elif internet_lower_bound <= sp <= internet_upper_bound:
        return create_switch_name(sp, internet_lower_bound, 'i')
    else:
        return f"{switch_name}"


def create_switch_name(sp, lower_bound, switch_char) -> str:
    new_sp = sp - lower_bound
    new_sp = new_sp + 1
    return f'{switch_char}{new_sp}'


def switch_from_host(path):
    ran_lower_bound = 1
    ran_upper_bound = 20
    metro_lower_bound = 21
    metro_upper_bound = 25
    access_lower_bound = 26
    access_upper_bound = 29
    core_lower_bound = 30
    core_upper_bound = 33
    internet_lower_bound = 34
    internet_upper_bound = 34

    path_first = path[0]
    path_rest = path[1:]
    switch_index = 0

    if path_first == 'r':
        switch_index = int(path_rest) + ran_lower_bound - 1
    elif path_first == 'm' and path[1] != 'a':
        switch_index = int(path_rest) + metro_lower_bound - 1
    elif path_first == 'a':
        switch_index = int(path_rest) + access_lower_bound - 1
    elif path_first == 'c' and path[1] != 'd':
        switch_index = int(path_rest) + core_lower_bound - 1
    elif path_first == 'i':
        switch_index = int(path_rest) + internet_lower_bound - 1

    if switch_index > 0:
        return 's' + str(switch_index)
    else:
        return path


def calculate_ip(p) -> str:
    if p == "cdn1":
        return "10.0.0.251"
    elif p == "cdn2":
        return "10.0.0.252"
    elif p == "cdn3":
        return "10.0.0.253"
    elif p == "ext1":
        return "10.0.0.254"
    elif p == "man1":
        return "10.0.0.241"
    elif p == "man2":
        return "10.0.0.242"
    elif p == "man3":
        return "10.0.0.243"
    elif p == "man4":
        return "10.0.0.244"
    elif p == "src1":
        return "10.0.0.249"
    elif p == "src2":
        return "10.0.0.250"
    else:
        pfirst = p[0]
        if pfirst in ['r', 'm', 'a', 'c', 'i', 's']:
            prest = switch_from_host(p)[1:]
            # prest = p[1:]
            ipfinal = 200 + int(prest)
            return f"10.0.0.{ipfinal}"
        elif pfirst == "u":
            ipfinal = p[1:]
            return f"10.0.0.{ipfinal}"
