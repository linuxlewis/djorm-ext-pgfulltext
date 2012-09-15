from setuptools import setup, find_packages

description="""
Pgfulltext module of django orm extensions package (collection of third party plugins build in one unified package).
"""

setup(
    name = "djorm-ext-pgfulltext",
    version = ':versiontools:djorm_pgfulltext:',
    url = 'https://github.com/niwibe/djorm-ext-pgfulltext',
    license = 'BSD',
    platforms = ['OS Independent'],
    description = description.strip(),
    author = 'Andrey Antukh',
    author_email = 'niwi@niwi.be',
    maintainer = 'Andrey Antukh',
    maintainer_email = 'niwi@niwi.be',
    packages = find_packages(),
    include_package_data = False,
    install_requires = [],
    setup_requires = [
        'versiontools >= 1.9',
    ],
    zip_safe = False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
