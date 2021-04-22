#!/bin/bash

print_help(){
    echo "-d(directory to be analyzed)"
    echo "-t"
    echo
}

DIR="./"
OUTPUT=".cur_tmp"
while getopts "d:t:o:h" arg
do
    case $arg in
	d)
	    DIR=$OPTARG;;
	t)
	    TIME=$OPTARG;;
	o)
	    OUTPUT=$OPTARG;;
	h)
	    print_help;;
    esac
done

if [[ ! -d $DIR ]]; then
    echo "Please input the directory with (-d)!"
    exit -1
fi

if [[ -z $TIME ]]; then
    echo "Please input the time"
fi

if [[ -f $OUTPUT ]]; then
    rm -f $OUTPUT
fi


cur_base_time=0
cur_end_time=0
cur_cnt=0
cur_idx=0

IFS=$'\n'
echo "time interval is $TIME" >> $OUTPUT
for cur_line in `find $DIR -name "id*" -printf "%T@ %p\n" | grep -v state | grep -E "pandoc|wkhtml|dharma|chrome" | grep sync | sort -n`; do
     cur_time=`echo $cur_line | cut -d ' ' -f1 | cut -d '.' -f1`

     if [[ $cur_base_time -eq 0 ]]; then
	 cur_base_time=$cur_time
	 cur_end_time=$((cur_time+TIME))
     fi

     while true; do
	 if [[ $cur_time -gt $cur_end_time ]]; then
	     echo "$cur_base_time, $cur_idx, $cur_cnt" >> $OUTPUT
	     cur_base_time=$cur_end_time
	     cur_end_time=$((cur_base_time+TIME))
	     cur_cnt=0
	     cur_idx=$((cur_idx+1))
	 else
	     cur_cnt=$((cur_cnt+1))
	     break
	 fi
     done
done	
echo "$cur_base_time, $cur_idx, $cur_cnt" >> $OUTPUT
echo "write the record to $OUTPUT"
