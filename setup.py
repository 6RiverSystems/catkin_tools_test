from setuptools import setup

setup(
    name='catkin_tools_test',
    packages=['catkin_tools_test'],
    version='0.0.0',
    author='Mike Purvis',
    author_email='mpurvis@clearpath.ai',
    maintainer='Mike Purvis',
    maintainer_email='mpurvis@clearpath.ai',
    url='http://catkin-tools-test.readthedocs.org/',
    keywords=['catkin'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
    ],
    description="Plugin for catkin_tools to enable building and running workspace tests.",
    license='Apache 2.0',
    entry_points={
        'catkin_tools.commands.catkin.verbs': [
            'tests = catkin_tools_test:description',
        ]
    },
    install_requires=['catkin_tools']
)
