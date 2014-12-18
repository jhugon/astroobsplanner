Astronomy Observability Planner
===============================

Astro Observability Planner is a GUI program that shows when an astronomical
object will be visible in the sky.  Times of observability are shown as regions
on a plot of time v. date. The program focuses on deep-sky objects (stars,
clusters, galaxies, etc.).  Astronomical object names or catalog numbers are
identified using the services at CDS (http://cdsweb.u-strasbg.fr/). Astro
Observability Planner is a Tk GUI using matplotlib, pyephem, and astropy.

Requirements
------------

Versions that have been shown to work in parenthesis

- numpy (1.7.1, 1.9.1)
- matplotlib, with TkAgg support (1.2.1, 1.4.2)
- astropy (0.4.2)
- pyephem (3.7.5.3)
- pytz (2012c, 2013.10)

Targets
-------

Uses CDS to look up the coordinates of deep-space objects.  Accepts "M33",
"HD125", "HIP12512", "Alpha Cent", and other designations. Coordinates are
locally cached on first look up.  The only solar-system objects supported are
the major planets (and Pluto).
