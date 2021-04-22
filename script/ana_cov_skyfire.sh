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
	d)
	    DIR=$OPTARG;;
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


cur_base_time=0
cur_end_time=0
cur_cnt=0
cur_idx=0
cur_cov=0

OLDIFS=$IFS
IFS=$'\n'
touch '.cur_cov'
echo "time interval is $TIME" >> $OUTPUT
for cur_line in `find $DIR -name "id*" -printf "%T@ %p\n" | grep -v state | grep queue | grep skyfire | sort -n -T "/home/ubuntu/fuzzing_mnt/tmp"`; do
     cur_time=`echo $cur_line | cut -d ' ' -f1 | cut -d '.' -f1`
     cur_file=`echo $cur_line | cut -d ' ' -f2`
     echo $cur_file
     run_cmd="afl-showmap -m none -o .cur_cov_tmp -- $CMD $cur_file"
     echo $run_cmd
     eval $run_cmd

     cat '.cur_cov' >> .cur_cov_tmp
     cat .cur_cov_tmp | sort | uniq > .cur_cov
     cur_cov=`cat .cur_cov | wc -l`

     if [[ $cur_base_time -eq 0 ]]; then
	 cur_base_time=$cur_time
	 cur_end_time=$((cur_time+TIME))
     fi

     while true; do
	 if [[ $cur_time -gt $cur_end_time ]]; then
	     echo "$cur_base_time, $cur_idx, $cur_cov"
	     echo "$cur_base_time, $cur_idx, $cur_cov" >> $OUTPUT
	     cur_base_time=$cur_end_time
	     cur_end_time=$((cur_base_time+TIME))
	     cur_idx=$((cur_idx+1))
	 else
	     break
	 fi
     done
done	
echo "$cur_base_time, $cur_idx, $cur_cnt" >> $OUTPUT
rm -f '.cur_cov'
echo "write the record to $OUTPUT"
