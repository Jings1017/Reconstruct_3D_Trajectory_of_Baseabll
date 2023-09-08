
echo $1
echo $2
OUTPUT_FILE1=$(echo $1 | sed 's/\.mp4/_poly.png/')
OUTPUT_FILE2=$(echo $2 | sed 's/\.mp4/_poly.png/')

echo 'input video1 : '$1;
echo 'input video2 : '$2;
echo 'output file1 : '$OUTPUT_FILE1;
echo 'output file2 : '$OUTPUT_FILE2;


python draw_poly_and_fill.py \
--video  $1 \
--output $OUTPUT_FILE1

python draw_poly_and_fill.py \
--video  $2 \
--output $OUTPUT_FILE2
