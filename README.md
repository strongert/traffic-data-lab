# traffic-data-lab
A project for processing and analyzing bus, taxi, and shared bike data.

This project focuses on extracting and processing public transit data near metro stations in Xi’an, using multi-source APIs and transportation datasets. It currently includes two main components:

 ## 📁 Files

- bus_processing.py  
  Extracts bus route and station data near selected Xi’an metro stations using the Amap (Gaode) API. Includes data filtering, structure transformation, and basic visualization support.

- taxi_processing.py  
  Processes taxi-related data (e.g. GPS trajectories or trip records) to identify spatial patterns and demand hotspots near metro areas.

- bycicle_processing.py

## 🔧 Features

- Integration with Amap API for transit data retrieval  
- Bus stop mapping and line association by metro station  
- Basic taxi data analysis (e.g. OD clustering, time-based distribution)
- Ready for downstream visualization (e.g. using Folium, Matplotlib)

## 🧪 Requirements

- Python 3.x  
- `pandas`  
- `requests`  
- `json`  
- `folium` (optional, for map visualization)  
- `geopandas` (optional, if spatial analysis is extended)

## 🌍 Application

This repository serves as a foundation for analyzing multimodal transit accessibility, identifying potential areas for service optimization near metro stations, and integrating bus/taxi/bycicle behavior for metro resilience studies.

## 📄 License

MIT License. Feel free to use or modify for academic or non-commercial projects.

