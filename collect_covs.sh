#!/bin/bash

while getopts "S:P:A:i:o:" arg
do 
    case $arg in 
	S)
	    SHOWMAP=$OPTARG;;
	P)
	    PDF_PARSER=$OPTARG;;
	A)
	    ARGS=$OPTARG;;
	i)
	    INPUT_DIR=$OPTARG;;
	o)
	    OUTPUT_DIR=$OPTARG;;
    esac
done

if [ -z $INPUT_DIR ]; then
    echo "Please give input directory with -i!"
    exit -1
fi

if [ -z $OUTPUT_DIR ]; then
    echo "Please give output directory with -o!"
fi

if [ ! -d $OUTPUT_DIR ]; then
    echo "mkdir $OUTPUT_DIR"
    mkdir -p $OUTPUT_DIR
fi

for queue in `find $INPUT_DIR -iname 'queue'`; do
    if [[ $queue != *slave* ]] && [[ $queue != *master* ]]; then
	continue
    fi

    for f in $queue/*; do

	if [ -d $f ]; then
	    continue
	fi

	base_name=`basename $f`

	if [[ $base_name == *sync* ]]; then
	    if [[ $base_name == *slave* ]] || [[ $base_name == *master* ]]; then
		continue
	    fi
	fi 

	modify_time=`stat -c %Y $f`
	cur_id=`echo $base_name | cut -d , -f1`
	cur_output=$OUTPUT_DIR/$modify_time-$cur_id

	if [ -f $cur_output ]; then
		echo "exists. skip"
		continue
	fi

	cur_input_cmd=${ARGS//@@/$f}

	cmd="$SHOWMAP -m none -o $cur_output -q -- $PDF_PARSER $cur_input_cmd"
	eval $cmd

    done

done
