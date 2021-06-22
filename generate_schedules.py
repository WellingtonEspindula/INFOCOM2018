#!/usr/bin/python3
import sys

def create_schedule(manager, manager_ip):
    has_tp = True
    has_rtt = True
    has_loss = True


    tp = "<plugins>throughput_tcp</plugins>" if has_tp else None
    rtt = "<plugins>rtt</plugins>" if has_rtt else None
    loss = "<plugins>loss</plugins>" if has_loss else None

    schedule = f"""<metrics>
    <ativas>
        <agt-index>1090</agt-index>
        <manager-ip>{manager_ip}</manager-ip>
        <literal-addr>1234</literal-addr>
        <android>1</android>
        <location>
            <name>837fc94b59e7b88a</name>
            <city>-</city>
            <state>-</state>
        </location>
        {tp}
        {rtt}
        {loss}
        <timeout>12</timeout>
        <probe-size>14520</probe-size>
        <train-len>1440</train-len>
        <train-count>1</train-count>
        <gap-value>100000</gap-value>
        <protocol>1</protocol>
        <num-conexoes>3</num-conexoes>
        <time-mode>2</time-mode>
        <max-time>12</max-time>
        <port>12001</port>
        <output>OUTPUT-SNMP</output>
    </ativas>
</metrics>"""

    with open(f'schedules/agent-fixa-{manager}.xml', 'w+') as file:
        file.write(schedule)


create_schedule('r1', '10.0.0.201')
create_schedule('r2', '10.0.0.202')
create_schedule('r3', '10.0.0.203')
create_schedule('r4', '10.0.0.204')
create_schedule('r5', '10.0.0.205')
create_schedule('r6', '10.0.0.206')
create_schedule('r7', '10.0.0.207')
create_schedule('r8', '10.0.0.208')
create_schedule('r9', '10.0.0.209')
create_schedule('r10', '10.0.0.210')
create_schedule('r11', '10.0.0.211')
create_schedule('r12', '10.0.0.212')
create_schedule('r13', '10.0.0.213')
create_schedule('r14', '10.0.0.214')
create_schedule('r15', '10.0.0.215')
create_schedule('r16', '10.0.0.216')
create_schedule('r17', '10.0.0.217')
create_schedule('r18', '10.0.0.218')
create_schedule('r19', '10.0.0.219')
create_schedule('r20', '10.0.0.220')
create_schedule('m1', '10.0.0.221')
create_schedule('m2', '10.0.0.222')
create_schedule('m3', '10.0.0.223')
create_schedule('m4', '10.0.0.224')
create_schedule('m5', '10.0.0.225')
create_schedule('a1', '10.0.0.226')
create_schedule('a2', '10.0.0.227')
create_schedule('a3', '10.0.0.228')
create_schedule('a4', '10.0.0.229')
create_schedule('c1', '10.0.0.230')
create_schedule('c2', '10.0.0.231')
create_schedule('c3', '10.0.0.232')
create_schedule('c4', '10.0.0.233')
create_schedule('i1', '10.0.0.234')

