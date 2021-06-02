from setuptools import find_packages, setup

setup(
    name="network_routing",
    packages=find_packages(),
    version="1.1.0",
    description="Python package to create and analyze routable networks",
    author="Aaron Fraint, AICP",
    license="MIT",
    entry_points="""
        [console_scripts]
        gaps=network_routing.gaps.cli:main
        access=network_routing.accessibility.cli:main
        db=network_routing.database.cli:main
        improvements=network_routing.improvements.cli:main
    """,
)
