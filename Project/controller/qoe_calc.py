import math


def appQoSStart(tp, loss, delay):
    if loss < 9:
        if tp >= 1400000:
            start = 0.89
        else:
            start = 2.2
        return start
    start = 20
    return start


def appQoSStcount(tp, loss, delay):
    # if tp < 680000:
    #    print "[SC] TP " + str(tp) + " DELAY " + str(delay)

    if tp >= 2000000:
        if tp >= 2300000:
            stcount = 0
        else:
            stcount = 1.8
    else:
        stcount = 10
    # if tp < 677000:
    #    if tp <= 400000:
    #        stcount = 7.5
    #    else:
    #        stcount = 6.5
    # else:
    #    if tp >= 1400000:
    #        stcount = 9.7
    #    else:
    #        stcount = 13
    # if tp < 680000:
    #    print "[SC] TP 2 " + str(tp) + " DELAY " + str(delay) + " STCOUNT: " + str(stcount)

    return stcount


def appQoSStlen(tp, loss, delay):
    stlen = None

    if tp >= 1400000:
        if tp >= 2000000:
            if tp >= 2500000:
                stlen = 0.039
            else:
                stlen = 1.2
        else:
            stlen = 33
    else:
        if tp >= 816000:
            if tp >= 977000:
                stlen = 58
            else:
                if delay < 0.064:
                    if tp >= 856000:
                        if delay < 0.056:
                            stlen = 68
                        else:
                            stlen = 69
                    else:
                        stlen = 71
                else:
                    stlen = 72
        else:
            if delay < 0.056:
                stlen = 73  # 70
            else:
                if tp >= 677000:
                    stlen = 82
                else:
                    if delay < 0.081:
                        if delay < 0.057:
                            stlen = 83
                        else:
                            stlen = 88
                    else:
                        stlen = 95

    return stlen

    #    def appQoSStcount(self, tp, loss, delay):
    #        if tp >= 2000000:
    #            if tp >= 2300000:
    #                stcount = 0
    #            else:
    #                stcount = 1.8
    #        else:
    #            if tp <= 677000:
    #                if tp <= 400000:
    #                    stcount = 7.5
    #                else:
    #                    stcount = 6.5
    #            else:
    #                stcount = 11
    #        return stcount
    #
    #    def appQoSStlen(self, tp, loss, delay):
    #        if tp >= 2000000:
    #            if tp >= 2500000:
    #                stlen = 0.029
    #            else:
    #                stlen = 1.2
    #        else:
    #            if tp >= 1400000:
    #                stlen = 33
    #            else:
    #                if tp >= 816000:
    #                    stlen = 67
    #                else:
    #                    if delay <= 0.056:
    #                        stlen = 70
    #                    else:
    #                        stlen = 86
    #        return stlen


def QoECalc(start, stcount, stlen):
    lam = float(stlen) / (stlen + 60.0)
    # if stlen > 80:
    #   print "STLEN: " + str(stlen) + " STCOUNT: " + str(stcount) + " LAMBDA: " + str(lam)
    if stcount > 1000:
        qoe = 1
        return qoe
    else:
        if lam < 0.1:
            a = 3.012682983
        elif lam < 0.2:
            a = 3.098391523
        elif lam < 0.579:
            a = 3.190341904
        elif lam < 0.586:  # 0.5
            #   print "A 0"
            a = 3.248113258
        else:  # 0.5
            #   print "A 1"
            a = 3.302343627
        if lam < 0.1:
            b = 0.765328992
        elif lam < 0.2:
            b = 0.994413063
        elif lam < 0.579:
            b = 1.520322299
        elif lam < 0.586:
            #   print "B 0"
            b = 1.693893480
        else:
            #   print "B 1"
            b = 1.888050118
        if lam < 0.1:
            c = 1.991000000
        elif lam < 0.2:
            c = 1.901000000
        elif lam < 0.579:
            c = 1.810138616
        elif lam < 0.586:
            # print "C 0"
            c = 1.751982415
        else:
            # print "C 1"
            c = 1.697472392
        qoe = a * math.exp(-b * stcount) + c
        # print "MOS: " + str(qoe)
        return qoe


def calculate_composed_mos(self, path):
    # print str(aux[0]) + " " + str(aux[1] + " " + str(bw[index1][index2]))

    final_bandwidth = 10000000000
    final_rtt = 0
    final_loss = 0
    for i in range(0, (len(path) - 1)):
        index2 = self.nodes.index(path[i + 1])
        index1 = self.nodes.index(path[i])
        final_bandwidth = self.bandwidths[index1][index2] if (
                self.bandwidths[index1][index2] < final_bandwidth) else final_bandwidth
        # print("FR: " + str(finalRtt) + " s: " + str(self.rtt[index1][index2]))
        final_rtt = self.rtt[index1][index2] + final_rtt

        loss_p = self.loss[index1][index2] / 100.0
        lossNode_p = final_loss / 100.0

        final_loss = 1 - ((1 - lossNode_p) * (1 - loss_p))
        final_loss = final_loss * 100

    start = appQoSStart(final_bandwidth, final_loss, final_rtt)
    stcount = appQoSStcount(final_bandwidth, final_loss, final_rtt)
    stlen = appQoSStlen(final_bandwidth, final_loss, final_rtt)
    mos = QoECalc(start, stcount, stlen)
    print("[RYU] CALCULADO BW: " + str(final_bandwidth) + " RTT: " + str(final_rtt) + " LOSS: " + str(
        final_loss) + " MOS: " + str(mos))
    return round(mos, 2)
