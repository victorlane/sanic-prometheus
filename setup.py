from setuptools import setup

from scripts.release import get_version

setup(
    name='sanic-prometheus',
    version=f'{get_version()}',
    description='Exposes Prometheus monitoring metrics of Sanic apps.',
    url='http://github.com/dkruchinin/sanic-prometheus',
    author='Dan Kruchinin',
    author_email='dan.kruchinin@gmail.com',
    license='MIT',
    packages=['sanic_prometheus'],
    zip_safe=False,
    platforms='any',
    python_requires='>=3.9',
    install_requires=[
        'sanic>=21.12',
        'prometheus-client>=0.16,<2.0',
        'psutil>=5.8.0'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Topic :: System :: Monitoring',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='sanic prometheus monitoring'
)
