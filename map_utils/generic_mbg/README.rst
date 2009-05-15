:Date: 15 May 2009
:Author: Anand Patil
:Contact: anand.prabhakar.patil@gmail.com
:Web site: github.com/malaria-atlas-project/map_utils
:Copyright: This document has been placed in the public domain.
:License: Creative Commons BY-NC-SA, see LICENSE


Overview
========

The generic MBG package allows us to write a PyMC probability model for a project's 
spatial or spatiotemporal count data (to a certain specification), then easily use 
it to fit a dataset & predict using the following three shell commands:

* ``mbg-infer`` runs the MCMC algorithm using the given model & an input dataset,
  stored in a csv file, and stores the traces in an HDF5 archive.

* ``mbg-map`` takes the HDF5 archive produced by mbg-infer, and an ASCII file with
  a MISSING entry in its header. Produces a set of bespoke summary maps on the grid
  expressed by the ASCII header. The missing pixels are missing in the output also.
  
* ``mbg-validate`` takes the HDF5 archive produced by mbg-infer and a 'holdout'
  dataset, stored in a csv file, and returns a set of predictive samples at the
  holdout locations.
  
If the project's members are interested in changing the model or specifying a
subjective prior, there are two additional shell commands available:

* ``mbg-scalar-priors`` draws samples from the prior for all scalar parameters
  (including deterministics) and plots histograms for inspection.
  
* ``mbg-realize-prior`` draws all scalar parameters from the prior, and realizes
  and plots the random field on grids matching a number of input ASCIIs.

***************************
Detailed usage instructions
***************************

=============
``mbg-infer``
=============