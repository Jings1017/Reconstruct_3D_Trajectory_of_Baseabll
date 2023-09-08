
echo $1
echo $2
OUTPUT_FILE1=$(echo $1 | sed 's/\.mp4/_coordinate.npy/')
OUTPUT_FILE2=$(echo $2 | sed 's/\.mp4/_coordinate.npy/')

echo 'input video1 : '$1;
echo 'input video2 : '$2;
echo 'output file1 : '$OUTPUT_FILE1;
echo 'output file2 : '$OUTPUT_FILE2;

python get_img_coordinate.py \
--video $1 \
--output $OUTPUT_FILE1

python get_img_coordinate.py \
--video $2 \
--output $OUTPUT_FILE2