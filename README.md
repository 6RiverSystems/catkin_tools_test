This package provides an extension for the catkin tools package. 

# Installation
From source:
1. Clone the repository
2. cd into the root folder
3. `sudo python setup.py develop`


# Usage
## verb: tests
This extension adds a new verb to the catkin tools package: `tests`. The word `test` overlaps with an alias that catkin tools already provides. 
To list all available tests:
`catkin tests --list` 
To run all tests:
`catkin tests`
To run only a subset of tests, you can pass a regular expression. Only tests whose names match the expression will run:
`catkin tests -t <RE>`
or
`catkin tests --tests <RE>`

To run only `rostest` tests, use
`catkin tests -t 'rostest_'*`


