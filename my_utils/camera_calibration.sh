echo 'input image folder : '$1;
echo 'output file path :'$2;
echo 'chessboard_size : '$3 $4;

python camera_calibration.py \
--input $1 \
--output $2 \
--chessboard_size $3 $4