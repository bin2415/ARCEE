#!/bin/bash

print_help(){
    echo "-o(output_dir)"
    echo
}
while getopts "o:h" arg
do
    case $arg in
	o)
	    OUTPUT_DIR=$OPTARG;;
	h)
	    print_help;;
    esac
done


if [[ ! -d $OUTPUT_DIR ]]; then
    echo "mkdir $OUTPUT_DIR"
    mkdir -p $OUTPUT_DIR
fi
echo $INPUT_DIR

chrome_out=$OUTPUT_DIR/chrome
wkhtml_out=$OUTPUT_DIR/wkhtml

if [[ ! -d $chrome_out ]]; then
    echo "mkdir $chrome_out"
    mkdir -p $chrome_out
fi

if [[ ! -d $wkhtml_out ]]; then
    echo "mkdir $wkhtml_out"
    mkdir -p $wkhtml_out
fi

#sleep 30m

iter_cnt=0
cur_cnt=0
valid_num=0
while true; do
    echo "==================current cnt $iter_cnt ==================="

    random_output=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
    tmp_output=${TMPDIR}/${random_output}.html

    python ./domato/generator.py $tmp_output

    output=`printf 'id:%06d,domato' $valid_num`

    cur_cnt=$((cur_cnt+1))
    
    output_wkhtml=${wkhtml_out}/wkhtml_${output}
    output_chrome=${chrome_out}/chrome_${output}
    
    echo $output
    
    if [ -f $output ]; then
	    echo "already exists, skip!"
	    valid_num=$((valid_num+1))
	    rm $tmp_output
	    continue
    fi

     echo "timeout 3s google-chrome --headless --disable-gpu --print-to-pdf=$output_chrome $tmp_output"
     timeout 3s google-chrome --headless --disable-gpu --print-to-pdf=$output_chrome $tmp_output
     timeout 3s wkhtmltopdf $tmp_output $output_wkhtml

     if [ $? -eq 0 ]; then
	valid_num=$((valid_num+1))
     fi

     rm $tmp_output

    echo "current valid num is $valid_num"
    iter_cnt=$((iter_cnt+1))

done
