#!/bin/bash
time=1800 # 30 mins
while getopts "i:" arg
do
    case $arg in
	i)
	    INPUT_DIR=$OPTARG;;
    esac
done

if [ -z $INPUT_DIR ]; then
    echo "Please input directory with -i!"
    exit -1
fi

start_time=0
cur_idx=0
for f in $INPUT_DIR/*; do
    if [ -d $f ]; then
	continue
    fi
    base_name=`basename $f`
    cur_time=`echo $base_name | cut -d '-' -f1 | awk '{print $1}'`

    if [ $start_time -eq 0 ]; then
	start_time=$cur_time
    fi

    bound_time=$((cur_time-$start_time))

    if [[ $bound_time -gt $time ]]; then
	echo "hello"
	start_time=$cur_time
	#cat $INPUT_DIR/.all_showmap_tmp | cut -d ':' -f1 | sort | uniq > $INPUT_DIR/.all_showmap
	cat $INPUT_DIR/.all_showmap_tmp | sort | uniq > $INPUT_DIR/.all_showmap
	cat $INPUT_DIR/.all_showmap | wc -l >> $INPUT_DIR/.showmap_list
	rm $INPUT_DIR/.all_showmap_tmp
	cp $INPUT_DIR/.all_showmap $INPUT_DIR/.all_showmap_tmp
    fi
    
    cat $f >> $INPUT_DIR/.all_showmap_tmp
done
cat $INPUT_DIR/.all_showmap_tmp | sort | uniq > $INPUT_DIR/.all_showmap
cat $INPUT_DIR/.all_showmap | wc -l >> $INPUT_DIR/.showmap_list
rm $INPUT_DIR/.all_showmap_tmp
rm $INPUT_DIR/.all_showmap
