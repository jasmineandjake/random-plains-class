for YEAR in "$@"
do
  # MACHINE=desktop-linux
  MACHINE=jake
  DEM=/media/${MACHINE}/my_book/dem_mosaic.tif
  FOLDER=/media/${MACHINE}/my_book/predict_imagery/${YEAR}_imagery
  NLCD=/media/jake/my_book/NLCD/NLCD_2001_Land_Cover_L48_20190424.img

  WORKING=$FOLDER/working
  FINISHED=$FOLDER/finished
  ALIGNED=$FOLDER/working/aligned

  SATELLITE=$FOLDER/${YEAR}.vrt
  CUTSAT=$WORKING/cutsat.tif
  CUTDEM=$WORKING/cutdem.tif
  CUTNLCD=$WORKING/cutnlcd.tif
  FILLEDDEM=$WORKING/filleddem.tif
  ALIGNEDSAT=$ALIGNED/sat.tif
  ALIGNEDEM=$ALIGNED/dem.tif
  ALIGNEDNLCD=$ALIGNED/nlcd.tif

  mkdir -p $WORKING
  mkdir -p $FINISHED
  mkdir -p $ALIGNED

  gdalbuildvrt -r lanczos $SATELLITE $FOLDER/*.tif

  python clipping_shp.py

  gdalwarp -cutline big_rect.shp -co NUM_THREADS=ALL_CPUS -crop_to_cutline $SATELLITE $CUTSAT
  gdalwarp -tr 30 30 -cutline big_rect.shp -co NUM_THREADS=ALL_CPUS -crop_to_cutline $DEM $CUTDEM
  gdalwarp -cutline big_rect.shp -co NUM_THREADS=ALL_CPUS -crop_to_cutline $NLCD $CUTNLCD

  python align_raster.py \
  -d $ALIGNEDSAT \
  -r $CUTSAT \
  -a $CUTNLCD \
  -t $WORKING

  gdal_fillnodata.py $CUTDEM $FILLEDDEM

  python align_raster.py \
  -d $ALIGNEDEM \
  -r $FILLEDDEM \
  -a $CUTNLCD \
  -t $WORKING

  cp $CUTNLCD $ALIGNEDNLCD

  # make slope and aspect from dem
  gdaldem aspect $FILLEDDEM $ALIGNED/aspect.tif -zero_for_flat
  gdaldem slope $FILLEDDEM $ALIGNED/slope.tif

  for f in $ALIGNED/*.tif; do
    echo "$f"
    name=${f##*/}
    base=${name%.tif}
    gdalwarp -cutline small_rect.shp -co NUM_THREADS=ALL_CPUS -crop_to_cutline "$f" $FINISHED/${base}_${YEAR}.tif
  done
done
