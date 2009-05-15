***********
Generic MBG
***********

:Date: 15 May 2009
:Author: Anand Patil
:Contact: anand.prabhakar.patil@gmail.com
:Web site: github.com/malaria-atlas-project/map_utils
:Copyright: This document has been placed in the public domain.
:License: Creative Commons BY-NC-SA
:Version: 2.0

Purpose
=======

The generic MBG subpackage allows us to write a PyMC probability model for spatial
or spatiotemporal count data (to a certain specification), then easily use it to fit 
a dataset & predict using the following three commands:

* ``mbg-infer`` runs the MCMC algorithm using the given model & an input dataset,
  stored in a csv file, and stores the traces in an HDF5 archive.

* ``mbg-map`` takes the HDF5 archive produced by mbg-infer, and an ASCII file with
  a MISSING entry in its header. Produces a set of bespoke summary maps on the grid
  expressed by the ASCII header. The missing pixels are missing in the output also.
  
* ``mbg-validate`` takes the HDF5 archive produced by mbg-infer and a 'holdout'
  dataset, stored in a csv file, and returns a set of predictive samples at the
  holdout locations.

Features
========

* Fits Bayesian statistical models you create with Markov chain Monte Carlo and
  other algorithms.

* Large suite of well-documented statistical distributions.

* Gaussian processes.

* Sampling loops can be paused and tuned manually, or saved and restarted later.

* Creates summaries including tables and plots.

* Traces can be saved to the disk as plain text, Python pickles, SQLite or MySQL
