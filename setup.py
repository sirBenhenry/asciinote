from setuptools import setup, find_packages

setup(
    name='asciicanvas',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'asciicanvas = asciicanvas.__main__:main',
        ],
    },
    install_requires=[
        'PySide6',
        'msgpack-python',
        'zstandard',
        'reportlab',
    ],
    python_requires='>=3.12',
)
