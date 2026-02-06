This code is used to extract data from LST file produce by the multiparameter system MPA-3 from the FastComteC GmbH company.
The system is used to realise PIXE maps.
Two MPA-3 channel must contained the analyse position (X,Y). the MPA-3 system must be configured with coincidence such as each event contained the X and Y position of the analyses point.
This code is used to retreive from the data stream each event and its corresponding position to generate the data cube of each detector channel.


The configuration file "config_lst2hdf5.ini" enable to set MPA channel and mpawin channels to extracted.

