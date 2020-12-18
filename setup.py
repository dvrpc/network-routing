from setuptools import find_packages, setup

setup(
    name="network_routing",
    packages=find_packages(),
    version="0.1.0",
    description="Python package to create and analyze routable networks",
    author="Aaron Fraint, AICP",
    license="MIT",
    entry_points="""
        [console_scripts]
        sidewalk=sidewalk_gaps.cli:main
        transit=transit_access.cli:main
    """,
)
