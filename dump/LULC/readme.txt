LULC stands for Land Use and Land Cover, a geospatial analysis technique that classifies and maps the Earth's surface based on its physical characteristics (land cover) and how it is used by humans (land use). Land cover refers to what the surface is made of, such as forests, water, or concrete, while land use describes human activities, like agriculture, residential areas, or industrial zones.

We have used three different datasets - MODIS, ESA WorldCover and Google Dynamic World.


The first is MODIS LC_Type1. This is a IGBP classification scheme and the only scheme that has an "urban" class. It is most widely used and well documented. Its spatial resolution is 500m meaning each pixel = 500 m × 500 m = 0.25 km² therefore it is not very well suited for details in a metropolitan city like Delhi. We have it here to analyse the general overall trends for the surrounding regions over the larger space.
For MODIS : 

	The encoding is that 
	909 means from class 9 in prev year to class 9 in this year.
	1313 means from class 13 in prev year to class 13 in this year.
	Why have conversion between same class ? Because we need continuity, stable land information.

	1213 means class 12 (which is cropland) changed to class 13 (which is urban)
	
ESA WorldCover has a spatial detail of 10m. The available dataset has cover for 2020 and 2021 only. We use this to get the most accurate change in the land cover.
Results from ESA WorldCover (from 2020 to 2021 only available)
	Total Green area converted to Built-up: 33.23 km²

	Total Cropland converted to Built-up: 11.99 km²

	--- Percentage Change ---
	Initial 2020 Cropland Area: 508.82 km²
	Percentage of 2020 Cropland lost to Built-up: 2.36%

	Initial 2020 Total Green Area: 782.15 km²
	Percentage of 2020 Green Cover lost to Built-up: 4.25%

Here, we have Google Dyanmic World which is a 10m spatial resolution, near real-time dataset for LULC. However we see that there are sudden spikes and sudden falls in the plot. We believe this is because of the terrible air quality conditions in Delhi.
Google World Cover :
		




