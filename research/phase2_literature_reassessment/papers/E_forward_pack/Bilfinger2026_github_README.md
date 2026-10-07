# Elsevier - eTransportation
# Battery pack diagnostics for electric vehicles: Robustness of the state of health measurement and differential voltage analysis at the vehicle level

Supplementary python code for the publication. Analyze charging data from state of the art electric vehicles.
Derive curves for vehicle level differential voltage analysis (DVA) and deeper aging assessment.

## Associated Article
Please also check the associated article available online published with eTransportation:
[Link to article](https://doi.org/10.1016/j.etran.2026.100589)
 
## Features
* Calculation of the vehicle-level SOH
* Calculation of DVA from timeseries data
* Availabilty vehicle data
* Filtering methods
* Notebooks for generatign images displayed in the article

## Project Structure
    ├── data           <- must be created by user, download files from mediatum (link below)
    │   │
    │   ├── font    <- fonts for the figures (STIX)
    │   │
    │   ├── Tesla    <- vehicle data for a Tesla Model 3 (LFP)
    │   │
    │   ├── Cupra    <- vehicle data for  Cupra Borns
    │   │
    │   └── VW       <- cell, halfcell and vehicle data
    │
    ├── figures    <- generated figures are saved here
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the category, and a short description 
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to load data for further processing
    │   │   
    │   ├── filtering       <- Filtering methods to reduce the noise in DVA/ICA
    │   │
    │   ├── visualization  <- Scripts to create visualizations
    │   │    
    │   └── voltage_capacity_analysis <- Scripts to extract the DVA from timeseries data
    │
    ├── .gitignore
    │
    ├── LICENSE
    │
    ├── README.md
    │	
    └── requirements.txt

## Requirements

The following requirements are to be met:
* python 3.11.9


## Installation

1. clone repo into directory
```console
git clone https://github.com/TUMFTM/EV_DVA_robustness
```  
2. install libraries via the requirements.txt
```console
pip install -r requirements.txt
```  
3. download data from mediaTUM and place into data folder:
```url
https://mediatum.ub.tum.de/1840112
```

## Contributing and Support

For contributing to the code please contact:  

[Philip Bilfinger](mailto:philip.bilfinger@tum.de)<br/>
**[Chair of Automotive Technology](https://www.mos.ed.tum.de/en/ftm/home/)**<br/>
**[Technical University of Munich, Germany](https://www.tum.de/en/)**

## Versioning

V0.1 

## Authors

Philip Bilfigner

## License
The MIT License (MIT)
Copyright (c) 2022, Philip Bilfinger

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Please refer to the license file for any further questions about incorporating these scripts into your projects.

We are looking forward to hearing your feedback and kindly ask you to share bugfixes, improvements and updates on the files provided.

Bibtex:

@article{BILFINGER2026100589,
title = {Battery pack diagnostics for electric vehicles: Robustness of the state of health measurement and differential voltage analysis at the vehicle level},
journal = {eTransportation},
pages = {100589},
year = {2026},
issn = {2590-1168},
doi = {https://doi.org/10.1016/j.etran.2026.100589},
url = {https://www.sciencedirect.com/science/article/pii/S2590116826000470},
author = {Philip Bilfinger and Philipp Rosner and Markus Schreiber and Tobias Brehler and Cristina Grosu and Jan Schöberl and Kareem {Abo Gamra} and Markus Lienkamp},
keywords = {Battery aging, Battery diagnostics, Differential voltage analysis, Electric vehicle, Lithium-ion battery, State of health},
}
