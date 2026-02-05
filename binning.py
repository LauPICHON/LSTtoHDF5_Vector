import numpy as np


def binning(data, bins):
    """
    Bin the data into specified bins.

    Parameters:
    data (array-like): The input data to be binned.
    bins (int or sequence of scalars): If an integer, it defines the number of equal-width bins in the range of the data.
                                       If a sequence, it defines the bin edges.

    Returns:
    tuple: A tuple containing:
        - binned_data: The binned data.
        - bin_edges: The edges of the bins.
    """
    T = np.arange(6 * 8 * 10).reshape(6, 8, 10)
    #T = np.ones((6, 8, 10))
    print(T.shape)  # Affiche (6, 8, 10)
    # Dimensions initiales
    N0, N1, N2 = T.shape    

    # Vérification que les dimensions 0 et 1 sont divisibles par 2
    assert N0 % 2 == 0 and N1 % 2 == 0
   # Reshape pour grouper par 2 sur les deux premiers axes
    T_reshaped = T.reshape(N0//2, 2, N1//2, 2, N2)
    print(T_reshaped.shape)  # Affiche (3, 2, 4, 2, 10)
# Agrégation par moyenne sur les axes regroupés
    T_grouped = T_reshaped.sum(axis=(1,3))
    print(T_grouped.shape)  # Affiche (3, 4, 10)
    #H1, xedges, yedges= np.histogram2d(,adc3,bins=(nb_column,nbcanaux),range= ({0, nb_column-1},{0, nbcanaux-1}))
    print(T_grouped[0, 0, :])  # Affiche la première "ligne" pour visualiser les valeurs    
    # a_grouped = a.reshape(4, 2).sum(axis=1)  # array([1, 5, 9, 13]) 
    # data_array = np.asarray(data)
    # H1, xedges, yedges= np.histogram2d(new_coord_y,adc3,bins=(nb_column,nbcanaux),range= ({0, nb_column-1},{0, nbcanaux-1}))
    # binned_data, bin_edges = np.histogram(data, bins=bins)
    #return binned_data, bin_edges
binning(10, 5) 