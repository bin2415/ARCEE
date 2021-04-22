#!/bin/bash

print_help(){
    echo "-o(output_dir)"
    echo
}

ITER_SEEDS=10000
while getopts "c:o:i:h" arg
do
    case $arg in
	o)
	    OUTPUT_DIR=$OPTARG;;
	h)
	    print_help;;
	c)
	    CMD=$OPTARG;;
	i)
	    ITER_SEEDS=$OPTARG;;
    esac
done

if [[ -z $OUTPUT_DIR ]]; then
    echo "Please add output with (-o <output dir>)"
    exit -1
fi

if [[ ! -d $OUTPUT_DIR ]]; then
    echo "mkdir $OUTPUT_DIR"
    mkdir -p $OUTPUT_DIR
fi

if [[ ! -f `which afl-cmin` ]]; then
    echo "Please install afl-cmin or add afl-cmin to PATH"
    exit -2
fi

echo $INPUT_DIR

#sleep 30m

iter_cnt=0
echo "hello"

valid_cnt=0
round_cnt=0
while true; do
    random_dir=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
    cmin_dir=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1` 
    mkdir -p $random_dir
    mkdir -p $cmin_dir
    valid_num=0

    while [[ $valid_num -lt $ITER_SEEDS ]]; do
	echo "==================current cnt $valid_num, round $round_cnt ==================="
	random_output=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
	tmp_output=/tmp/${random_output}

	output_file=${tmp_output}/1.html

	dharma -grammars dharma/dharma/grammars/canvas2d.dg -template dharma/dharma/grammars/var/templates/html5/default.html -storage $tmp_output

	output=`printf 'tmp:%06d,domato' $valid_num`
	output=${random_dir}/${output}

	echo $output
	timeout 3s google-chrome --headless --disable-gpu --print-to-pdf=$output $output_file
	if [ $? -eq 0 ]; then
	    valid_num=$((valid_num+1))
	fi

	rm -r $tmp_output
    done


    echo "==================afl-cmin: at round $round_cnt ============================"
    # firstly, append seeds in queue to $random_dir
    for cur_f in `ls $OUTPUT_DIR`; do
	cp ${OUTPUT_DIR}/${cur_f} $random_dir
    done

    afl-cmin -m none -i $random_dir -o $cmin_dir -- $CMD

    # copy the minimized seeds to output
    for cur_f in `ls $cmin_dir`; do
	if [ -f ${OUTPUT_DIR}/${cur_f} ]; then
	    continue
	fi
	valid_cnt=$((valid_cnt+1))
	dst=`printf 'id:%06d,domato' $valid_cnt`
	cp ${cmin_dir}/${cur_f} ${OUTPUT_DIR}/${dst}
    done

    round_cnt=$((round_cnt+1))
    rm -r $random_dir
    rm -r $cmin_dir

done
