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

#sleep 30m

iter_cnt=0
cur_cnt=0
valid_num=0
while true; do
    echo "==================current cnt $iter_cnt ==================="

    random_output=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
    tmp_output=${random_output}.html

    python ./domato/generator.py $tmp_output

    output_name=`printf 'id:%06d,domato.pdf' $valid_num`

    cur_cnt=$((cur_cnt+1))
    
    output=${OUTPUT_DIR}/${output_name}
    
    echo $output
    
    if [ -f $output ]; then
	    echo "already exists, skip!"
	    valid_num=$((valid_num+1))
	    rm $tmp_output
	    continue
    fi

    #pandoc -f html -t pdf $tmp_output -o $output
    timeout 1m docker run --rm --volume "`pwd`:/data" --user `id -u`:`id -g` pandoc/latex:latest -f html $tmp_output -o $output_name
    mv $output_name $output

     if [ -f $output ]; then
	valid_num=$((valid_num+1))
     fi

     rm $tmp_output

    echo "current valid num is $valid_num"
    iter_cnt=$((iter_cnt+1))
done
