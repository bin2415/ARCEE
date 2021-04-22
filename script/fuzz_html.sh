#!/bin/bash

print_help(){
    echo "-d(directory to be analyzed)"
    echo "-t"
    echo
}

DIR="./"
OUTPUT=".cur_tmp"
while getopts "d:t:o:c:h" arg
do
    case $arg in
	t)
	    TIME=$OPTARG;;
	o)
	    OUTPUT=$OPTARG;;
	c)
	    CMD=$OPTARG;;
	h)
	    print_help;;
    esac
done

if [[ ! -d $DIR ]]; then
    echo "Please input the directory with (-d)!"
    exit -1
fi

if [[ ! -f `which afl-showmap` ]]; then
    echo "Please install afl-showmap or add afl-showmap to PATH"
    exit -2
fi

if [[ -z $TIME ]]; then
    echo "Please input the time"
fi

if [[ -z $CMD ]]; then
    echo "Please input commands with (-c)!"
    exit -1
fi

if [[ -f $OUTPUT ]]; then
    rm -f $OUTPUT
fi

cur_base_time=`date +%s`
cur_end_time=$((cur_base_time+TIME))
cur_idx=0
cur_cov=0

cur_file_idx=0

OLDIFS=$IFS
IFS=$'\n'
cur_cov_sum=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
cur_cov_tmp=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
touch $cur_cov_sum
echo "time interval is $TIME" >> $OUTPUT

cur_dir=`dirname $0`

trap ctrl_c INT
function ctrl_c(){
    echo "stoping... $cur_base_time, $cur_idx, $cur_cov"
    echo "$cur_base_time, $cur_idx, $cur_cov" > $OUTPUT
    rm $cur_cov_sum
    rm $cur_cov_tmp
    exit -1
}

while true; do
    cur_date=`date +%s`
    if [[ $cur_date -gt $cur_end_time ]]; then
	echo "$cur_base_time, $cur_idx, $cur_cov"
	echo "$cur_base_time, $cur_idx, $cur_cov" >> $OUTPUT
	cur_base_time=$cur_date
	cur_end_time=$((cur_base_time+TIME))
	cur_idx=$((cur_idx+1))
    fi

    ## generate html
    random_output=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
    tmp_output=/tmp/${random_output}.html
    python $cur_dir/domato/generator.py  $tmp_output
    echo $tmp_output

    run_cmd="timeout 3s afl-showmap -m none -o $cur_cov_tmp -- $CMD $tmp_output"
    echo $run_cmd
    eval $run_cmd
    rm $tmp_output

    cmd="cat ${cur_cov_sum} >> ${cur_cov_tmp}"
    echo $cmd
    eval $cmd
    cmd="cat ${cur_cov_tmp} | sort | uniq > ${cur_cov_sum}"
    echo $cmd
    eval $cmd

    cur_cov=`cat $cur_cov_sum | wc -l`
done

