GROVERBUFFER=/home/jake/scripts/land_cover/Multi_buffer2.shp
WELLINGTONBUFFER=/home/jake/scripts/land_cover/multi_ring4.shp

LIST=( 1987 1990 1993 1996 1999 2002 2005 2008 2011 2014 2017 1986 1989 1992 1995 1998 2001 2004 2007 2010 2013 2016 1985 1988 1991 1994 1997 2000 2003 2006 2009 2012 2015 )
for YEAR in "${LIST[@]}"
do
  INPUT=/home/jake/scripts/land_cover/transitions/$YEAR.tif
  OUTPUTGROVER=/home/jake/scripts/land_cover/transition_clipped_years/grover_$YEAR.tif
  OUTPUTWELLINGTON=/home/jake/scripts/land_cover/transition_clipped_years/wellington_$YEAR.tif
  gdalwarp -cutline $GROVERBUFFER -crop_to_cutline $INPUT $OUTPUTGROVER
  gdalwarp -cutline $WELLINGTONBUFFER -crop_to_cutline $INPUT $OUTPUTWELLINGTON
done
