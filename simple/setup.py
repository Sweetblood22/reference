from distutils.core import setup

setup(
    name='surrogate',
    version='0.0.1',
    packages=['simple', 'simple.trees'],
    url='www.spa.com',
    license='N/A',
    author='Josh McCrary',
    author_email='jmccrary@spa.com',
    description='Simulation for inventory and maintenance policies and logistic events',
    requires=['numpy'],
    package_dir={'simple': 'simple',
                 'simple.trees': 'trees'},
    package_data={'simple': ['examples/*.json', 'examples/*.csv']}
)
