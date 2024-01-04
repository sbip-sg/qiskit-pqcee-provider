import setuptools

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
README = (this_directory / "README.md").read_text()
REQUIREMENTS = [
    "qiskit[visualization]",
    "web3[tester]",
    "py-solc-x",
]

setuptools.setup(
    name='qiskit_pqcee_provider',
    version='0.1.0',
    description='A qiskit provider on the blockchain.',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/sdcioc/qiskit-pqcee-provider',
    author='Stefan-Dan Ciocirlan (sdcioc)',
    author_email='stefan_dan@xn--ciocirlan-o2a.ro',
    license='MIT',
    packages=setuptools.find_packages(exclude=["test*"]),
    package_data={"qiskit_pqcee_provider": ["contracts/*.sol",
                                            "mumbai_testnet_config.ini"]},
    install_requires=REQUIREMENTS,
    classifiers=[
        "Intended Audience :: Developers",
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.6, <4",
    zip_safe=False,
    include_package_data=True,
)