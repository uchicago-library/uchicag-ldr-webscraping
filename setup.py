from distutils.core import setup

setup(
    name = 'uchicagoldr-webscraping',
    version = '0.0.1',
    author = "Brian Balsamo",
    author_email = "balsamo@uchicago.edu",
    packages = ['ldrwebscraping'],
    description = """\
    A set of base classes for interacting with University of Chicago library 
    digital repository objects
    """,
    keywords = ["uchicago","repository","web","scraping"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    long_description = open('README.md').read(),
    install_requires = ['requests',
                        'bs4',
                        'uchicagoldr'])
