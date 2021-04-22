#!/bin/bash

print_help(){
    echo "-o(output_dir)"
    echo "-s(skyfire output)"
    echo
}

skyfire_root='/home/ubuntu/fuzzing_mnt/skyfire_hb/src'
skyfire_output='/home/ubuntu/fuzzing_mnt/skyfire_hb/html_gen'

while getopts "s:o:h" arg
do
    case $arg in
	o)
	    OUTPUT_DIR=$OPTARG;;
	s)
	    SKYFIRE_OUTPUT=$OPTARG;;
	h)
	    print_help;;
    esac
done

if [[ ! -d $OUTPUT_DIR ]]; then
    echo "mkdir $OUTPUT_DIR"
    mkdir -p $OUTPUT_DIR
fi

if [[ ! -d $SKYFIRE_OUTPUT ]]; then
    echo "mkdir -p $SKYFIRE_OUTPUT"
    mkdir -p $SKYFIRE_OUTPUT
fi

if [[ -d $skyfire_output ]]; then
    rm ${skyfire_output}/*
else
    mkdir -p $skyfire_output
fi

iter_cnt=0
cur_cnt=0
html_id=0
valid_num_chrome=0
valid_num_wkhtml=0
valid_num_pandoc=0

chrome_output=${OUTPUT_DIR}/chrome_slave_skyfire/queue
wkhtml_output=${OUTPUT_DIR}/wkhtml_slave_skyfire/queue

if [[ ! -d $chrome_output ]]; then
    mkdir -p $chrome_output
fi

if [[ ! -d $wkhtml_output ]]; then
    mkdir -p $wkhtml_output
fi

while true; do
    echo "==================current cnt $iter_cnt ==================="

    pushd $PWD
    cd ${skyfire_root}
    
    # generate html
    python run_cmd.py

    popd

    for html_i in ${skyfire_output}/*; do

	html_output=`printf 'skyfire:%06d.html' $html_id`
	cp ${html_i} ${SKYFIRE_OUTPUT}/${html_output}
	html_id=$((html_id+1))

	output=`printf 'id:%06d,skyfire' $valid_num_chrome`
	timeout 3s google-chrome --headless --disable-gpu --print-to-pdf=${chrome_output}/${output} $html_i

	if [ $? -eq 0 ]; then
	    valid_num_chrome=$((valid_num_chrome+1))
	fi

	output=`printf 'id:%06d,skyfire' $valid_num_wkhtml`
	timeout 3s xvfb-run wkhtmltopdf -l $html_i ${wkhtml_output}/${output}

	if [ $? -eq 0 ]; then
	    valid_num_wkhtml=$((valid_num_wkhtml+1))
	fi
    done

    rm ${skyfire_output}/*


    echo "current valid num is $valid_num"
    iter_cnt=$((iter_cnt+1))
done
