
CONVERTOR_ARR=(google-chrome wkhtmltopdf)
# CONVERTOR_ARR=(wkhtmltopdf)

REPLACE_FONT_RATE=8 # 0.8 * 10
DECOMPRESS_RATE=8 # 0.8 * 10

# this is the commands that run convertors. The format is:
#   first argument is input html file
#   second argument is input pdf file
CONVERTOR_CMD_ARR=("google-chrome --headless --no-sandbox --disable-gpu %s --print-to-pdf=%s" "wkhtmltopdf -l %s %s")

convert_htmls_to_pdfs(){

  input_dir=$1
  output_dir=$2
  idx=$3
  cur_convertor=${CONVERTOR_ARR[$idx]}
  valid_num_tmp=0
  for f in $input_dir/*; do

    cur_output=${output_dir}/`printf "id:%06d,%s.pdf" $valid_num_tmp $cur_convertor`
    echo $cur_output

    cmd=`printf "timeout 3s ${CONVERTOR_CMD_ARR[$idx]}" $f $cur_output`

    eval $cmd > /dev/null 2>&1

    if [ -f $cur_output ]; then
      echo -en "\r\t\t Convertor ${CONVERTOR_ARR[$i]} generate pdf $cur_output succeed!"
      valid_num_tmp=$((valid_num_tmp+1))
    fi

  done
}

convert_htmls_to_pdfs /home/ubuntu/fuzzing_mnt/tmp_output/google-chrome_20201221140129/.trim_html /home/ubuntu/fuzzing_mnt/tmp_output/google-chrome_20201221140129/.trim_html_pdf 0 
