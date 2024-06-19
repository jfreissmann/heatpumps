from setuptools import find_packages, setup

with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='heatpumps',
    version='1.0.0',
    author='Jonas Freißmann, Malte Fritz',
    author_email='jonas.freissmann@web.de',
    description='Collection of TESPy heat pump models and additional Streamlit dashboard.',
    long_description_content_type='text/markdown',
    long_description=long_description,
    url='https://github.com/jfreissmann/heatpumps',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        'heatpumps': [
            'static/*',
            'static/img/*',
            'static/img/topologies/*',
            'models/input/*'
        ]
    },
    python_requires='>=3.9',
    install_requires=[
        'tespy>=0.7.0',
        'streamlit>=1.32.0',
        'numpy>=1.24.0',
        'pandas>=1.5.3',
        'scipy>=1.10.0',
        'scikit-learn>=1.2.1',
        'matplotlib>=3.6.3',
        'fluprodia>=2.0',
        'coolprop>=6.4.1',
        'darkdetect>=0.8.0',
        'plotly>=5.20.0',
    ],
    entry_points={
        'console_scripts': [
            'heatpumps-dashboard=heatpumps.run_dashboard:main',
        ]
    }
)
