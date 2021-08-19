# TODO Improve it using Regex
def switch_from_host(self, path):
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


def host_from_switch(self, path):
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

    if path_first == 's':
        switch_index = int(path_rest)
        if ran_lower_bound <= switch_index <= ran_upper_bound:
            rindex = switch_index - ran_lower_bound + 1  # se switch_index = 3, p.e., 3 - 1 + 1 = 3
            return "r" + str(rindex)
        elif metro_lower_bound <= switch_index <= metro_upper_bound:
            mindex = switch_index - metro_lower_bound + 1  # se switch_index = 21, p.e., 21 - 21 + 1 = 1
            return "m" + str(mindex)
        elif access_lower_bound <= switch_index <= access_upper_bound:
            aindex = switch_index - access_lower_bound + 1
            return "a" + str(aindex)
        elif core_lower_bound <= switch_index <= core_upper_bound:
            cindex = switch_index - core_lower_bound + 1
            return "c" + str(cindex)
        elif internet_lower_bound <= switch_index <= internet_upper_bound:
            iindex = switch_index - internet_lower_bound + 1
            return "i" + str(iindex)
        else:
            return path
    else:
        return path


def ip_from_host(self, host):
    if host == "src1":
        return "10.0.0.249"
    elif host == "src2":
        return "10.0.0.250"
    elif host == "cdn1":
        return "10.0.0.251"
    elif host == "cdn2":
        return "10.0.0.252"
    elif host == "cdn3":
        return "10.0.0.253"
    elif host == "ext1":
        return "10.0.0.254"
    elif host == "man1":
        return "10.0.0.241"
    elif host == "man2":
        return "10.0.0.242"
    elif host == "man3":
        return "10.0.0.243"
    elif host == "man4":
        return "10.0.0.244"
    else:
        first = host[0]
        if first == 'u':
            ipfinal = host.split("u")[1]
            return "10.0.0." + str(int(ipfinal))  # para remover os leading zeros
        elif first == 'r' or first == 'm' or first == 'a' or first == 'c' or first == 'i' or first == 's':
            sn = self.switch_from_host(host)
            print("LOCAL SN: " + sn)
            restsn = sn[1:]
            ipfinal = 200 + int(restsn)
            return "10.0.0." + str(ipfinal)


def deploy_any_path(self, path):
    paths = [path, path[::-1]]
    for path in paths:
        for i in range(1, len(path) - 1):
            # instaling rule for the i switch
            sn = self.switch_from_host(path[i])
            dpid = int(sn[1:])
            _next = self.switch_from_host(path[i + 1])
            datapath = self.datapaths[dpid]
            parser = datapath.ofproto_parser
            ofproto = datapath.ofproto

            out_port = self.edges_ports["s%s" % dpid][_next]
            actions = [parser.OFPActionOutput(out_port)]
            self.logger.info("installing rule from %s to %s %s %s", path[i], path[i + 1], str(path[0][1:]),
                             str(path[-1][1:]))
            ip_src = self.ip_from_host(str(path[0]))  # to get the id
            ip_dst = self.ip_from_host(str(path[-1]))
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst)
            self.add_flow(datapath, 1024, match, actions)
    self.current_path = path