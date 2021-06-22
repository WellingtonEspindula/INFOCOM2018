#!/bin/bash

cpuroundrobin=0
CPU_LIMIT=4

#Startup time prediction
function appQoSStart()
{
  tp=`echo $1 | cut -d '.' -f 1`
  loss=`echo $2 | cut -d '.' -f 1`
  delay=`echo $3 \* 1000.0 | bc |  cut -d '.' -f 1`

  if [ $loss -lt 9 ]
  then
    if [ $tp -ge 1400000 ]
    then
      startuptime="0.89"
    else
      startuptime="2.2"
    fi
  else
    startuptime=20
  fi
}

#Stall count prediction
function appQoSStcount()
{
  tp=`echo $1 | cut -d '.' -f 1`
  loss=`echo $2 | cut -d '.' -f 1`
  delay=`echo $3 \* 1000.0 | bc |  cut -d '.' -f 1`


  if [ $tp -ge 2000000 ]
  then
    if [ $tp -ge 2300000 ]
    then
      stcount=0
    else
      stcount="1.8"
    fi   
  else
    if [ $tp -le 677000 ]
    then
      if [ $tp -le 400000 ]
      then
        stcount="7.5"
      else
        stcount="6.5"
      fi
    else
      stcount=11
    fi
  fi
}


#Total stall length prediction

function appQoSStlen()
{
  tp=`echo $1 | cut -d '.' -f 1`
  loss=`echo $2 | cut -d '.' -f 1`
  delay=`echo $3 \* 1000.0 | bc |  cut -d '.' -f 1`
  echo "DELAY" $delay
  if [ $tp -ge 2000000 ]
  then
    if [ $tp -ge 2500000 ]
    then
      stlen="0.029"
    else
      stlen="1.2"
    fi
  else
    if [ $tp -ge 1400000 ]
    then
      stlen="33"
    else
      if [ $tp -ge 816000 ]
      then
        stlen="67"
      else
        if [ $delay -le 56 ]
        then
          stlen="70"
        else
          stlen="86"
        fi
      fi
    fi
  fi
}

function QoECalc()
{
  lambda=`echo $stlen / \($stlen + 60.0\) | bc -l`
	
  if [ $(bc <<< "$stcount > 6.0") -eq 1 ]
  then
    qoe="1.0"
  else
    if [ $(bc <<< "$lambda < 0.05") -eq 1 ]
    then
      a="3.012682983"
      b="0.765328992"
      c="1.991000000"
    elif [ $(bc <<< "$lambda < 0.1") -eq 1 ]
    then
      a="3.098391523"
      b="0.994413063"
      c="1.901000000"
    elif [ $(bc <<< "$lambda < 0.2") -eq 1 ]
    then
      a="3.190341904"
      b="1.520322299"
      c="1.810138616"
    elif [ $(bc <<< "$lambda < 0.5") -eq 1 ]
    then
      a="3.248113258"
      b="1.693893480"
      c="1.751982415"
    else
      a="3.302343627"
      b="1.888050118"
      c="1.697472392"
    fi
    qoe=`echo $a \* e\(-$b \* $stcount\) + $c | bc -l`
  fi
}

function xml_to_csv()
{
  rm -f nm_last_results.txt
  rm -f nm_last_results.csv

  #Preenchendo os pseudo_results de hosts
  phost=1
  while [ $phost -le 200 ]
  do
    rindex=`expr $phost / 10`

    redondo=`expr $phost % 10`
    if [ ! $redondo -eq 0 ]
    then
      rindex=`expr $rindex + 1`
    fi
    fillphost=`printf %03d $phost`
    echo "u$fillphost;r$rindex;0.000000;0.000000;10000000000" >> nm_last_results.txt #atraso zero, perda zero, tp infinito
    echo "r$rindex;u$fillphost;0.000000;0.000000;10000000000" >> nm_last_results.txt
    phost=`expr $phost + 1`
  done
  

  for file in results/*
  do
    BASENAME=$(basename $file .xml)
    agent=$(cut -d '-' -f1 <<< $BASENAME)
    if [ "$agent" == "agent" ]
    then
      P1=$(cut -d '-' -f2 <<< $BASENAME)
      P2=$(cut -d '-' -f3 <<< $BASENAME)
      UDP_RESULTS=$(sed 's/<?.*//' <<< $(awk 'NR==2' $file))
      TCP_RESULTS=$(awk 'NR==3' $file)
      RTT=$(xmllint --xpath '//results/ativas[@metrica="rtt"]/upavg/text()' - <<< $UDP_RESULTS)
      OWD=$(bc <<< "scale=6;$RTT/2")
      LOSSUP=$(xmllint --xpath '//results/ativas[@metrica="loss"]/upavg/text()' - <<< $UDP_RESULTS)
      LOSSDOWN=$(xmllint --xpath '//results/ativas[@metrica="loss"]/downavg/text()' - <<< $UDP_RESULTS)
      TCPUP=$(xmllint --xpath '//results/ativas[@metrica="throughput_tcp"]/upavg/text()' - <<< $TCP_RESULTS)
      TCPDOWN=$(xmllint --xpath '//results/ativas[@metrica="throughput_tcp"]/downavg/text()' - <<< $TCP_RESULTS)
      #echo "$P1;$P2;$RTT;$LOSSUP;$LOSSDOWN;$TCPUP;$TCPDOWN" >> nm_last_results.txt
      echo "$P1;$P2;$OWD;$LOSSDOWN;$TCPDOWN" >> nm_last_results.txt
      echo "$P2;$P1;$OWD;$LOSSUP;$TCPUP" >> nm_last_results.txt
    fi
  done
  cp -f nm_last_results.txt nm_last_results.csv
}

function specific_xml_to_csv()
{
  P1=$1 #agente
  P2=$2 #gerentao
  cd results  
  file="agent-"$P2"-"$P1".xml"
  
  UDP_RESULTS=$(sed 's/<?.*//' <<< $(awk 'NR==2' $file))
  TCP_RESULTS=$(awk 'NR==3' $file)
  RTT=$(xmllint --xpath '//results/ativas[@metrica="rtt"]/upavg/text()' - <<< $UDP_RESULTS)
  OWD=$(bc <<< "scale=6;$RTT/2")
  LOSSUP=$(xmllint --xpath '//results/ativas[@metrica="loss"]/upavg/text()' - <<< $UDP_RESULTS)
  LOSSDOWN=$(xmllint --xpath '//results/ativas[@metrica="loss"]/downavg/text()' - <<< $UDP_RESULTS)
  TCPUP=$(xmllint --xpath '//results/ativas[@metrica="throughput_tcp"]/upmin/text()' - <<< $TCP_RESULTS)
  TCPDOWN=$(xmllint --xpath '//results/ativas[@metrica="throughput_tcp"]/downmin/text()' - <<< $TCP_RESULTS)
  sxc="$P2;$P1;$OWD;$LOSSDOWN;$TCPDOWN"
  sxc2="$P1;$P2;$OWD;$LOSSUP;$TCPUP"
  cd -
}

RAN_LOWER_BOUND=1
RAN_UPPER_BOUND=20

METRO_LOWER_BOUND=21
METRO_UPPER_BOUND=25

ACCESS_LOWER_BOUND=26
ACCESS_UPPER_BOUND=29

CORE_LOWER_BOUND=30
CORE_UPPER_BOUND=33

INTERNET_LOWER_BOUND=34
INTERNET_UPPER_BOUND=34

function rename_switch()
{
  switchname=$1
  sp=${switchname:1}
  if [ $sp -ge $RAN_LOWER_BOUND -a $sp -le $RAN_UPPER_BOUND ]
  then
    newsp=`expr $sp - $RAN_LOWER_BOUND`
    newsp=`expr $newsp + 1`
    echo "r$newsp"
  elif [ $sp -ge $METRO_LOWER_BOUND -a $sp -le $METRO_UPPER_BOUND ]
  then
    newsp=`expr $sp - $METRO_LOWER_BOUND`
    newsp=`expr $newsp + 1`
    echo "m$newsp"
  elif [ $sp -ge $ACCESS_LOWER_BOUND -a $sp -le $ACCESS_UPPER_BOUND ]
  then
    newsp=`expr $sp - $ACCESS_LOWER_BOUND`
    newsp=`expr $newsp + 1`
    echo "a$newsp"
  elif [ $sp -ge $CORE_LOWER_BOUND -a $sp -le $CORE_UPPER_BOUND ]
  then 
    newsp=`expr $sp - $CORE_LOWER_BOUND`
    newsp=`expr $newsp + 1`
    echo "c$newsp"
  elif [ $sp -ge $INTERNET_LOWER_BOUND -a $sp -le $INTERNET_UPPER_BOUND ]
  then 
    newsp=`expr $sp - $INTERNET_LOWER_BOUND`
    newsp=`expr $newsp + 1`
    echo "i$newsp"
  else
    echo "$switchname"
  fi
}

function is_number()
{
  yournumber=$1
  re='^[0-9]+$'
  if ! [[ $yournumber =~ $re ]]
  then
    echo "0"
  else
    echo "1"
  fi
}

function test_enabled(){
  p1=$1
  p2=$2
  
  p1first=${p1:0:1}
  p2first=${p2:0:1}

  p1rest=${p1:1}
  p2rest=${p2:1}

  p1n=`is_number $p1rest`
  p2n=`is_number $p2rest`

  p1switch=0
  p2switch=0

  if [ "$p1first" = "s" -a $p1n -eq 1 ]
  then
    p1switch=1
  fi

  if [ "$p2first" = "s" -a $p2n -eq 1 ]
  then
    p2switch=1
  fi

  p1host=0
  p2host=0
#  Estou comentando as linhas de baixo - sempre que pelo menos um dos terminais for host, nao ha mais medicao.
#  if [ "$p1first" = "u" ]
#  then
#     p1host=1
#  fi

#  if [ "$p2first" = "u" ]
#  then
#     p2host=1
#  fi

  p1first3=${p1:0:3}
  p2first3=${p2:0:3}

  p1src=0
  p2src=0

  if [ "$p1first3" = "ext" -o "$p1first3" = "cdn" -o "$p1first3" = "src" ]
  then
    p1src=1
  fi

  if [ "$p2first3" = "ext" -o "$p2first3" = "cdn" -o "$p2first3" = "src" ]
  then
    p2src=1
  fi

  if [ $p1switch -eq 1 -o $p1host -eq 1 -o $p1src -eq 1 ] && [ $p2switch -eq 1 -o $p2host -eq 1 -o $p2src -eq 1 ]
  then
    echo "1"
  else
    echo "0"
  fi
}


function calculate_ip()
{
  p=$1
  if [ "$p" = "src1" ]
  then
    echo "10.0.0.249"
  elif [ "$p" = "src2" ]
  then
    echo "10.0.0.250"
  elif [ "$p" = "cdn1" ]
  then
    echo "10.0.0.251"
  elif [ "$p" = "cdn2" ]
  then
    echo "10.0.0.252"
  elif [ "$p" = "cdn3" ]
  then
    echo "10.0.0.253"
  elif [ "$p" = "ext1" ]
  then
    echo "10.0.0.254"
  else
     pfirst=${p:0:1}
     if [ "$pfirst" = "s" ]
     then
       prest=${p:1}
       ipfinal=`expr 200 + $prest`
       echo "10.0.0.$ipfinal"
     elif [ "$pfirst" = "u" ]
     then
       ipfinal=`echo $p | cut -d 'u' -f 2`
       ipfinal=`expr $ipfinal + 0`
       echo "10.0.0.$ipfinal"
     fi
  fi

}

function perform_measurement()
{
  p1=$1 #agente
  p2=$2 #gerente
  cp1=${p1:0:1}
  cp2=${p2:0:1}

  #se o segundo for um "u", nao pode ser gerente. Inverter
  #if [ "$cp2"   = "u" ]
  #then
  #  aux=$p1
  #  p1=$p2
  #  p2=$aux
  #  cp1=${p1:0:1}
  #  cp2=${p2:0:1}
  #fi


  enabled=`test_enabled $p1 $p2`
  if [ $enabled -eq 1 ]
  then
    ip1=`calculate_ip $p1`
    ip2=`calculate_ip $p2`
 
    sp1=${p1:1}
    sp2=${p2:1}
    sp1n=`is_number $sp1`
    sp2n=`is_number $sp2`
    #echo $p1 $p2 $cp1 $cp2
    if [ "$cp1" = "s" -a $sp1n -eq 1 ]
    then
      p1=`rename_switch $p1`
    fi
    if [ "$cp2" = "s" -a $sp2n -eq 1 ]
    then
      p2=`rename_switch $p2`
    fi

    echo "AGENT $p1 ($ip1), MANAGER $p2 ($ip2)"

    agent=$p1
    manager=$p2
    managerip=$ip2

    cp -f /home/mininet/manconfs/agent-fixa-$manager.xml /tmp/agent-fixa-$manager-$agent.xml
    sed -i "s/<literal-addr>.*<\/literal-addr>/<literal-addr>$agent<\/literal-addr>/g" /tmp/agent-fixa-$manager-$agent.xml 
    cd results
    managerip="10.0.0."$manageripfinal
    #echo $managerip
    cpuroundrobin=`expr $cpuroundrobin % $CPU_LIMIT`
    taskset -c 4-19 /home/mininet/mininet/util/m $agent metricagent -c -f /tmp/agent-fixa-$manager-$agent.xml -w -l 1000 -u 100 -u $manager-$agent -i 0 &
    cpuroundrobin=`expr $cpuroundrobin + 1`
#    /home/mininet/mininet/util/m $agent iperf3 -c $managerip 2&> iperf-$manager-$agent -n 5048000
    cd -
#    echo "Silvio Santos $agent $manager"
#   rm -rf /tmp/agent-fixa-$manager-$agent.xml
#   exit 0
  fi
}

sources=('src1' 'src2' 'cdn1' 'cdn2' 'cdn3' 'ext1')
hosts=('u001')

HEATMAPFILE=$1
killall -9 metricmanager
killall -9 iperf3
rm -rf results/*

for i in `ls manconfs`
do
  echo "******"
  echo $i
  manager=`echo $i | cut -d '.' -f 1 | cut -d'-' -f 3`
  freeport=`/home/mininet/mininet/util/m $manager netstat -anp | tr -s " \t" | cut -d' ' -f 4 | grep 12055`
  while [ -n "$freeport" ]
  do
    echo "Aguardando liberacao da porta no gerente $manager..."
    freeport=`/home/mininet/mininet/util/m $manager netstat -anp | tr -s " \t" | cut -d' ' -f 4 | grep 12055`
    sleep 0.5
  done
  cpuroundrobin=`expr $cpuroundrobin % $CPU_LIMIT`
  taskset -c 4-19 /home/mininet/mininet/util/m $manager metricmanager -c &
  cpuroundrobin=`expr $cpuroundrobin + 1`
#  /home/mininet/mininet/util/m $manager iperf3 -s &
done

rm -f bestpaths.serialize
rm -f cursing_videos_secure.csv

while true
do
  rm -f results/*
  metricagent_start=`date +%s`
  while read line
  do
    p1=`echo $line | cut -d' ' -f 1` #agente
    p2=`echo $line | cut -d' ' -f 2` #gerente
    perform_measurement $p1 $p2
  done < net.edgelist
 
  ma=`ps auxf | grep -v "grep" | grep metricagent`
  while [ -n "$ma" ]
  do
    echo "Metricagent ainda rodando..."
    sleep 0.5
    ma=`ps auxf | grep -v "grep" | grep metricagent`
  done
  metricagent_stop=`date +%s`
  metricagent_diff=`expr $metricagent_stop - $metricagent_start` 
  echo "Metricagent: FIM (TEMPO: $metricagent_diff segundos)"
  xml_to_csv

#exit 0

  if [ -e "cursing_videos.csv" ]
  then
    rm -f cursing_videos_secure.csv
    cp -f cursing_videos.csv cursing_videos_secure.csv
  fi


  deploy_start=`date +%s`
  curl -X GET http://127.0.0.1:8080/bqoepath/bestqoepath-all-all > /tmp/deployresult-all-all.json &
  
  dpl=`ps auxf | grep -v "grep" | grep bestqoepath`
  while [ -n "$dpl" ]
  do
    echo "Deploy de rotas ainda rodando..."
    sleep 0.1
    dpl=`ps auxf | grep -v "grep" | grep bestqoepath`
  done
  deploy_stop=`date +%s`
  deploy_diff=`expr $deploy_stop - $deploy_start` 
  echo "DEPLOY: FIM (TEMPO: $deploy_diff segundos)"
  
  #CALCULAR MOS DOS VIDEOS EM CURSO

  if [ -e "cursing_videos_secure.csv" ]
  then
    #rm -f cursing_videos_secure.csv
    #cp -f cursing_videos.csv cursing_videos_secure.csv
    rm -f /tmp/lstats.csv
    python link_stats.py cursing_videos_secure.csv > /tmp/lstats.csv
    statsheader=`head -n 1 /tmp/lstats.csv`
    statsinfo=`tail -n 1 /tmp/lstats.csv`

    statsheaderexists=`cat $HEATMAPFILE | grep $statsheader`
    if [ ! -n "$statsheaderexists" ]
    then
        echo "$statsheader" >> $HEATMAPFILE
    fi
    echo "$statsinfo" >> $HEATMAPFILE
  fi

  sleep 15
  #ma=`ps auxf | grep -v "grep" | grep metricagent`
  #while [ -n "$ma" ]
  #do
  #  echo "Metricagent ainda rodando..."
  #  sleep 0.5
  #  ma=`ps auxf | grep -v "grep" | grep metricagent`
  #done
  #echo "Metricagent: FIM"
  #xml_to_csv
done
#specific_xml_to_csv "h1" "h99"
#delaydown=`echo $sxc | cut -d ';' -f 3`
#lossdown=`echo $sxc | cut -d ';' -f 4`
#tpdown=`echo $sxc | cut -d ';' -f 5`

#delayup=`echo $sxc2 | cut -d ';' -f 3`
#lossup=`echo $sxc2 | cut -d ';' -f 4`
#tpup=`echo $sxc2 | cut -d ';' -f 5`


#echo "<<<" $delaydown $lossdown $tpdown $delayup $lossup $tpup

#appQoSStart $tpdown $lossdown $delaydown
#appQoSStcount $tpdown $lossdown $delaydown
#appQoSStlen $tpdown $lossdown $delaydown
#echo ">>>" $startuptime $stcount $stlen
#QoECalc
#echo "QoE de DOWNLOAD (ponto de vista de H1): $qoe"

#appQoSStart $tpup $lossup $delayup
#appQoSStcount $tpup $lossup $delayup
#appQoSStlen $tpup $lossup $delayup
#QoECalc
#echo "QoE de UPLOAD (ponto de vista de H1): $qoe"
