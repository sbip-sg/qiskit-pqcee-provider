# Download base image ubuntu 22.04
FROM ubuntu:22.04

# LABEL about the custom image
LABEL maintainer="dancioc@nus.edu.sg"
LABEL version="0.1"
LABEL description="This is a custom Docker Image for Qiskit pQCee provider"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive
# display
ENV DISPLAY=host.docker.internal:0.0
# timezone
ENV TZ=Asia/Singapore

# Update Ubuntu Software repository
# https://stackoverflow.com/questions/39760663/docker-ubuntu-bin-sh-1-locale-gen-not-found
# https://askubuntu.com/questions/162391/how-do-i-fix-my-locale-issue/229512#229512
# add etherum ppa
# install python/pip/cmake/solc/sphinx
RUN apt-get update && apt upgrade -y && apt-get install -y locales && locale-gen "en_US.UTF-8" && dpkg-reconfigure locales && \
    apt-get install -y software-properties-common && apt-get update && add-apt-repository ppa:ethereum/ethereum && apt-get update && \
    apt-get install -y curl zip unzip git cmake sphinx python3 python3-pip python3-sphinx solc

# install python packages qiskit/qiskit-aer/pydata_sphinx_theme/sphinx-autodoc-typehints/sphinx-autoapi/web3/py-solc-x/twine
RUN pip3 install qiskit[visualization] && pip3 install qiskit-aer && pip3 install pydata_sphinx_theme && pip3 install sphinx-autodoc-typehints && \
    pip3 install sphinx-autoapi && pip3 install sphinxcontrib-autoprogram && pip3 install web3[tester] && pip install py-solc-x && pip3 install twine