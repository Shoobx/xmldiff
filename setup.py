from setuptools import setup, find_packages

version = "2.5.dev0"

with open("README.rst", encoding="utf8") as readme:
    description = readme.read()

with open("CHANGES.rst", encoding="utf8") as changes:
    history = changes.read()


setup(
    name="xmldiff",
    version=version,
    description="Creates diffs of XML files",
    long_description=description + "\n" + history,
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Text Processing :: Markup :: XML",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="xml html diff",
    author="Lennart Regebro",
    author_email="lregebro@shoobx.com",
    url="https://github.com/Shoobx/xmldiff",
    license="MIT",
    packages=find_packages(exclude=["doc", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "lxml>=3.1.0",
        "six",
    ],
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "xmldiff = xmldiff.main:diff_command",
            "xmlpatch = xmldiff.main:patch_command",
        ],
    },
)
